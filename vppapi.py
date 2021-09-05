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


logger = logging.getLogger('pyagentx.vppapi')
logger.addHandler(NullHandler())

vpp_lock = threading.Lock()


def vpp_connect():
    global logger

    vpp_json_dir = '/usr/share/vpp/api/'

    # construct a list of all the json api files
    jsonfiles = []
    for root, dirnames, filenames in os.walk(vpp_json_dir):
        for filename in fnmatch.filter(filenames, '*.api.json'):
            jsonfiles.append(os.path.join(root, filename))

    if not jsonfiles:
        logger.error('no json api files found')
        return False

    vpp = VPPApiClient(apifiles=jsonfiles, server_address='/run/vpp/api.sock')
    try:
        vpp.connect('vpp-snmp-agent')
    except:
        return False

    v = vpp.api.show_version()
    logger.info('VPP version is %s' % v.version)

    return vpp


def get_iface(vpp, ifname):
    global logger

    vpp_lock.acquire()
    iface_list = vpp.api.sw_interface_dump(name_filter=ifname,
                                           name_filter_valid=True)
    if not iface_list:
        logger.error("Can't get interface %s" % ifname)
        vpp_lock.release()
        return None

    for iface in iface_list:
        if iface.interface_name == ifname:
            vpp_lock.release()
            return iface
    vpp_lock.release()
    return None


def get_ifaces(vpp):
    global logger

    vpp_lock.acquire()
    ret = {}
    iface_list = vpp.api.sw_interface_dump()
    if not iface_list:
        logger.error("Can't get interface list")
        vpp_lock.release()
        return ret

    for iface in iface_list:
        ret[iface.interface_name] = iface

    vpp_lock.release()
    return ret
