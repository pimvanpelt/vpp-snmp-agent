'''
The functions in this file interact with the VPP API to retrieve certain
interface metadata.
'''

from vpp_papi import VPPApiClient
import os
import fnmatch
import logging
import socket


class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('agentx.vppapi')
logger.addHandler(NullHandler())


class VPPApi():
    def __init__(self, address='/run/vpp/api.sock', clientname='vppapi-client'):
        self.address = address
        self.connected = False
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
            logger.error('no json api files found')
            return False

        self.vpp = VPPApiClient(apifiles=jsonfiles,
                                server_address=self.address)
        try:
            logger.info('Connecting to VPP')
            self.vpp.connect(self.clientname)
        except:
            return False

        v = self.vpp.api.show_version()
        logger.info('VPP version is %s' % v.version)

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
            logger.error("VPP communication error, disconnecting", e)
            self.vpp.disconnect()
            self.connected = False
            return ret

        if not iface_list:
            logger.error("Can't get interface list")
            return ret

        for iface in iface_list:
            ret[iface.interface_name] = iface

        return ret

    def get_lcp(self):
        ret = {}
        if not self.connected:
            return ret


        try:
            lcp_list = self.vpp.api.lcp_itf_pair_get()
        except Exception as e:
            logger.error("VPP communication error, disconnecting", e)
            self.vpp.disconnect()
            self.connected = False
            return ret

        if not lcp_list or not lcp_list[1]:
            logger.error("Can't get LCP list")
            return ret

        ## TODO(pim) - fix upstream, the indexes are in network byte order and
        ## the message is messed up. This hack allows for both little endian and
        ## big endian responses, and will be removed once VPP's LinuxCP is updated
        ## and rolled out to AS8298
        for lcp in lcp_list[1]:
            if lcp.phy_sw_if_index > 65535 or lcp.host_sw_if_index > 65535 or lcp.vif_index > 65535:
                i = {
                  'phy_sw_if_index': socket.ntohl(lcp.phy_sw_if_index),
                  'host_sw_if_index': socket.ntohl(lcp.host_sw_if_index),
                  'vif_index': socket.ntohl(lcp.vif_index),
                  'host_if_name': lcp.host_if_name,
                  'namespace': lcp.namespace
                  }
            else:
                i = {
                  'phy_sw_if_index': lcp.phy_sw_if_index,
                  'host_sw_if_index': lcp.host_sw_if_index,
                  'vif_index': lcp.vif_index,
                  'host_if_name': lcp.host_if_name,
                  'namespace': lcp.namespace
                  }
            ret[lcp.host_if_name] = i
        return ret
