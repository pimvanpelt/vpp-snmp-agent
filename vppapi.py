'''
The functions in this file interact with the VPP API to retrieve certain
interface metadata.
'''

from vpp_papi import VPPApiClient
import os
import fnmatch
import logging
import threading


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


class VPPApi():
    def __init__(self, address='/run/vpp/api.sock'):
        self.address = address
        self.lock = threading.Lock()
        self.connected = False
        self.logger = logging.getLogger('pyagentx.vppapi')
        self.logger.addHandler(NullHandler())
        self.vpp = None

    def connect(self):
        self.lock.acquire()
        if self.connected:
            self.lock.release()
            return True

        vpp_json_dir = '/usr/share/vpp/api/'

        # construct a list of all the json api files
        jsonfiles = []
        for root, dirnames, filenames in os.walk(vpp_json_dir):
            for filename in fnmatch.filter(filenames, '*.api.json'):
                jsonfiles.append(os.path.join(root, filename))

        if not jsonfiles:
            self.logger.error('no json api files found')
            self.lock.release()
            return False

        self.vpp = VPPApiClient(apifiles=jsonfiles,
                                server_address=self.address)
        try:
            self.logger.info('Connecting to VPP')
            self.vpp.connect('vpp-snmp-agent')
        except:
            self.lock.release()
            return False

        v = self.vpp.api.show_version()
        self.logger.info('VPP version is %s' % v.version)

        self.connected = True
        self.lock.release()
        return True

    def disconnect(self):
        if not self.connected:
            return True
        self.vpp.disconnect()
        self.connected = False
        return True

    def get_ifaces(self):
        ret = {}
        if not self.connected:
            return ret

        self.lock.acquire()
        try:
            iface_list = self.vpp.api.sw_interface_dump()
        except Exception as e:
            self.logger.error("VPP communication error, disconnecting", e)
            self.vpp.disconnect()
            self.connected = False
            self.lock.release()
            return ret

        if not iface_list:
            self.logger.error("Can't get interface list")
            self.lock.release()
            return ret

        for iface in iface_list:
            ret[iface.interface_name] = iface

        self.lock.release()
        return ret
