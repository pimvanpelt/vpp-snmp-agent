"""
The functions in this file interact with the VPP API to retrieve certain
interface metadata.
"""

from vpp_papi import VPPApiClient, VPPApiJSONFiles
import os
import fnmatch
import logging
import socket


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger("agentx.vppapi")
logger.addHandler(NullHandler())


class VPPApi:
    def __init__(self, address="/run/vpp/api.sock", clientname="vppapi-client"):
        self.address = address
        self.connected = False
        self.clientname = clientname
        self.vpp = None

    def connect(self):
        if self.connected:
            return True

        vpp_json_dir = VPPApiJSONFiles.find_api_dir([])
        vpp_jsonfiles = VPPApiJSONFiles.find_api_files(api_dir=vpp_json_dir)
        if not vpp_jsonfiles:
            logger.error("no json api files found")
            return False

        self.vpp = VPPApiClient(apifiles=vpp_jsonfiles, server_address=self.address)
        try:
            logger.info("Connecting to VPP")
            self.vpp.connect(self.clientname)
        except:
            return False

        v = self.vpp.api.show_version()
        logger.info("VPP version is %s" % v.version)

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

        if not lcp_list:
            logger.error("Can't get LCP list")
            return ret

        for lcp in lcp_list[1]:
            ret[lcp.host_if_name] = lcp
        return ret
