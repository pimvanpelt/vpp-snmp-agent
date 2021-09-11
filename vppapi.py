'''
The functions in this file interact with the VPP API to retrieve certain
interface metadata.
'''

from vpp_papi import VPPApiClient
import os
import fnmatch
import logging


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


class VPPApi():
    def __init__(self, address='/run/vpp/api.sock', clientname='vppapi-client'):
        self.address = address
        self.connected = False
        self.logger = logging.getLogger('agentx.vppapi')
        self.logger.addHandler(NullHandler())
        self.clientname = clientname
        self.vpp = None

    def connect(self):
        if self.connected:
            return True

        vpp_json_dir = '/usr/share/vpp/api/'

        # construct a list of all the json api files
        jsonfiles = []
        for root, dirnames, filenames in os.walk(vpp_json_dir):
            for filename in fnmatch.filter(filenames, '*.api.json'):
                jsonfiles.append(os.path.join(root, filename))

        if not jsonfiles:
            self.logger.error('no json api files found')
            return False

        self.vpp = VPPApiClient(apifiles=jsonfiles,
                                server_address=self.address)
        try:
            self.logger.info('Connecting to VPP')
            self.vpp.connect(self.clientname)
        except:
            return False

        v = self.vpp.api.show_version()
        self.logger.info('VPP version is %s' % v.version)

        self.connected = True
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

        try:
            iface_list = self.vpp.api.sw_interface_dump()
        except Exception as e:
            self.logger.error("VPP communication error, disconnecting", e)
            self.vpp.disconnect()
            self.connected = False
            return ret

        if not iface_list:
            self.logger.error("Can't get interface list")
            return ret

        for iface in iface_list:
            ret[iface.interface_name] = iface

        return ret
