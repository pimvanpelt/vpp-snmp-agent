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
        self.iface_dict = None
        self.lcp_dict = None

    def _sw_interface_event(self, event):
        # NOTE(pim): this callback runs in a background thread, so we just clear the
        # cached interfaces and LCPs here, subsequent call to get_ifaces() or get_lcp()
        # will refresh them in the main thread.
        logger.info(f"Clearing iface and LCP cache due to interface event")
        self.iface_dict = None
        self.lcp_dict = None

    def _event_callback(self, msg_type_name, msg_type):
        logger.debug(f"Received callback: {msg_type_name} => {msg_type}")
        if msg_type_name == "sw_interface_event":
            self._sw_interface_event(msg_type)
        else:
            logger.warning(f"Ignoring unkonwn event: {msg_type_name} => {msg_type}")

    def connect(self):
        if self.connected:
            return True

        vpp_json_dir = VPPApiJSONFiles.find_api_dir([])
        vpp_jsonfiles = VPPApiJSONFiles.find_api_files(api_dir=vpp_json_dir)
        if not vpp_jsonfiles:
            logger.error("no json api files found")
            return False

        self.vpp = VPPApiClient(apifiles=vpp_jsonfiles, server_address=self.address)
        self.vpp.register_event_callback(self._event_callback)
        try:
            logger.info("Connecting to VPP")
            self.vpp.connect(self.clientname)
        except:
            return False

        v = self.vpp.api.show_version()
        logger.info("VPP version is %s" % v.version)

        logger.info("Enabling VPP API interface events")
        r = self.vpp.api.want_interface_events(enable_disable=True)
        if r.retval != 0:
            logger.error("Could not enable VPP API interface events, disconnecting")
            self.disconnect()
            return False

        self.connected = True
        return True

    def disconnect(self):
        if not self.connected:
            return True
        self.vpp.disconnect()
        self.iface_dict = None
        self.lcp_dict = None
        self.connected = False
        return True

    def get_ifaces(self):
        ret = {}
        if not self.connected and not self.connect():
            logger.warning("Can't connect to VPP API")
            return ret

        if type(self.iface_dict) is dict:
            logger.debug("Returning cached interfaces")
            return self.iface_dict

        ret = {}
        try:
            logger.info("Requesting interfaces from VPP API")
            iface_list = self.vpp.api.sw_interface_dump()
        except Exception as e:
            logger.error("VPP API communication error, disconnecting", e)
            self.disconnect()
            return ret

        if not iface_list:
            logger.error("Can't get interface list, disconnecting")
            self.disconnect()
            return ret

        for iface in iface_list:
            ret[iface.interface_name] = iface

        self.iface_dict = ret
        logger.debug(f"Caching interfaces: {ret}")
        return self.iface_dict

    def get_lcp(self):
        ret = {}
        if not self.connected and not self.connect():
            logger.warning("Can't connect to VPP API")
            return ret

        if type(self.lcp_dict) is dict:
            logger.debug("Returning cached LCPs")
            return self.lcp_dict

        try:
            logger.info("Requesting LCPs from VPP API")
            lcp_list = self.vpp.api.lcp_itf_pair_get()
        except Exception as e:
            logger.error("VPP communication error, disconnecting", e)
            self.disconnect()
            return ret

        if not lcp_list:
            logger.error("Can't get LCP list")
            return ret

        for lcp in lcp_list[1]:
            ret[lcp.host_if_name] = lcp

        self.lcp_dict = ret
        logger.debug(f"Caching LCPs: {ret}")
        return self.lcp_dict
