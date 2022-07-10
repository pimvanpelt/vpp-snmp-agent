#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vppstats import VPPStats
from vppapi import VPPApi
import sys
import yaml
import agentx

try:
    import argparse
except ImportError:
    print("ERROR: install argparse manually: sudo pip install argparse")
    sys.exit(2)

def get_phy_by_sw_if_index(ifaces, sw_if_index):
    try:
        for k,v in ifaces.items():
            if v.sw_if_index == sw_if_index:
                return v
    except:
        pass
    return None


def get_lcp_by_host_sw_if_index(lcp, host_sw_if_index):
    try:
        for k,v in lcp.items():
            if v.host_sw_if_index == host_sw_if_index:
                return v
    except:
        pass
    return None


def get_description_by_ifname(config, ifname):
    try:
        for phy_name, phy in config['interfaces'].items():
            if ifname == phy_name:
                return phy['description']
            if 'sub-interfaces' in phy:
                for sub_id, sub_int in config['interfaces'][phy_name]['sub-interfaces'].items():
                    sub_ifname = "%s.%d" % (phy_name, sub_id)
                    if ifname == sub_ifname:
                        return sub_int['description']
    except:
        pass
    return None


class MyAgent(agentx.Agent):
    def setup(self):
        global vppstat, vpp, logger, args

        self.config = None
        if args.config:
            try:
                with open(args.config, "r") as f:
                    self.logger.info("Loading configfile %s" % args.config)
                    self.config = yaml.load(f, Loader = yaml.FullLoader)
                    self.logger.debug("Config: %s" % self.config)
            except:
                self.logger.error("Couldn't read config from %s" % args.config)

        try:
            self.logger.info("Connecting to VPP Stats Segment")
            vppstat = VPPStats(socketname='/run/vpp/stats.sock', timeout=2)
            vppstat.connect()
        except:
            self.logger.error("Could not connect to VPPStats segment")
            return False

        try:
            vpp = VPPApi(clientname='vpp-snmp-agent')
            vpp.connect()
        except:
            self.logger.error("Could not connect to VPP API")
            return False

        self.register('1.3.6.1.2.1.2.2.1')
        self.register('1.3.6.1.2.1.31.1.1.1')

        return True


    def update(self):
        global vppstat, vpp, args

        try:
            vppstat.connect()
        except:
            self.logger.error("Could not connect to VPPStats segment")
            return False

        try:
            vpp.connect()
        except:
            self.logger.error("Could not connect to VPP API")
            return False

        ds = agentx.DataSet()
        ifaces = vpp.get_ifaces()
        lcp = vpp.get_lcp()

        num_ifaces=len(ifaces)
        num_vppstat=len(vppstat['/if/names'])
        num_lcp=len(lcp)
        self.logger.debug("LCP: %s" % (lcp))
        self.logger.debug("Retrieved Interfaces: vppapi=%d vppstats=%d lcp=%d" % (num_ifaces, num_vppstat, num_lcp))

        if num_ifaces != num_vppstat:
            self.logger.error("Interfaces count mismatch: vppapi=%d vppstats=%d" % (num_ifaces, num_vppstat))
            return False

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            idx = 1000+i

            ds.set('1.3.6.1.2.1.2.2.1.1.%u' % (idx), 'int', idx)

            ifName=ifname
            ifAlias=None
            try:
                if self.config and ifname.startswith('tap'):
                    host_sw_if_index = ifaces[ifname].sw_if_index
                    lip = get_lcp_by_host_sw_if_index(lcp, host_sw_if_index)
                    if lip:
                        phy = get_phy_by_sw_if_index(ifaces, lip.phy_sw_if_index)
                        ifName = lip.host_if_name
                        self.logger.debug("Setting ifName of %s to '%s'" % (ifname, ifName))
                        if phy:
                            ifAlias = "LCP %s (%s)" % (phy.interface_name,ifname)
                            self.logger.debug("Setting ifAlias of %s to '%s'" % (ifname, ifAlias))
            except:
                self.logger.debug("No config entry found for ifname %s" % (ifname))
                pass

            ds.set('1.3.6.1.2.1.2.2.1.2.%u' % (idx), 'str', ifName)

            if ifname.startswith("loop"):
                ds.set('1.3.6.1.2.1.2.2.1.3.%u' % (idx), 'int', 24)  # softwareLoopback
            else:
                ds.set('1.3.6.1.2.1.2.2.1.3.%u' % (idx), 'int', 6)   # ethermet-csmacd

            mtu = 0
            if not ifname in ifaces:
                self.logger.warning("Could not get MTU for interface %s", ifname)
            else:
                mtu = ifaces[ifname].mtu[0]
            ds.set('1.3.6.1.2.1.2.2.1.4.%u' % (idx), 'int', mtu)

            speed = 0
            if ifname.startswith("loop") or ifname.startswith("tap"):
                speed = 1000000000
            elif not ifname in ifaces:
                self.logger.warning("Could not get link speed for interface %s", ifname)
            else:
                speed = ifaces[ifname].link_speed * 1000
            if speed >= 2**32:
                speed = 2**32 - 1
            ds.set('1.3.6.1.2.1.2.2.1.5.%u' % (idx), 'gauge32', speed)

            mac = "00:00:00:00:00:00"
            if not ifname in ifaces:
                self.logger.warning("Could not get PhysAddress for interface %s", ifname)
            else:
                mac = str(ifaces[ifname].l2_address)
            ds.set('1.3.6.1.2.1.2.2.1.6.%u' % (idx), 'str', mac)

            admin_status = 3  # testing
            if not ifname in ifaces:
                self.logger.warning("Could not get AdminStatus for interface %s", ifname)
            else:
                if int(ifaces[ifname].flags) & 1:
                    admin_status = 1  # up
                else:
                    admin_status = 2  # down
            ds.set('1.3.6.1.2.1.2.2.1.7.%u' % (idx), 'int', admin_status)

            oper_status = 3  # testing
            if not ifname in ifaces:
                self.logger.warning("Could not get OperStatus for interface %s", ifname)
            else:
                if int(ifaces[ifname].flags) & 2:
                    oper_status = 1  # up
                else:
                    oper_status = 2  # down
            ds.set('1.3.6.1.2.1.2.2.1.8.%u' % (idx), 'int', oper_status)

            ds.set('1.3.6.1.2.1.2.2.1.9.%u' % (idx), 'ticks', 0)
            ds.set('1.3.6.1.2.1.2.2.1.10.%u' % (idx), 'u32', vppstat['/if/rx'][:, i].sum_octets() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.11.%u' % (idx), 'u32', vppstat['/if/rx'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.12.%u' % (idx), 'u32', vppstat['/if/rx-multicast'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.13.%u' % (idx), 'u32', vppstat['/if/rx-no-buf'][:, i].sum() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.14.%u' % (idx), 'u32', vppstat['/if/rx-error'][:, i].sum() % 2**32)

            ds.set('1.3.6.1.2.1.2.2.1.16.%u' % (idx), 'u32', vppstat['/if/tx'][:, i].sum_octets() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.17.%u' % (idx), 'u32', vppstat['/if/tx'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.18.%u' % (idx), 'u32', vppstat['/if/tx-multicast'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.19.%u' % (idx), 'u32', vppstat['/if/drops'][:, i].sum() % 2**32)
            ds.set('1.3.6.1.2.1.2.2.1.20.%u' % (idx), 'u32', vppstat['/if/tx-error'][:, i].sum() % 2**32)

            ds.set('1.3.6.1.2.1.31.1.1.1.1.%u' % (idx), 'str', ifName)
            ds.set('1.3.6.1.2.1.31.1.1.1.2.%u' % (idx), 'u32', vppstat['/if/rx-multicast'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.31.1.1.1.3.%u' % (idx), 'u32', vppstat['/if/rx-broadcast'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.31.1.1.1.4.%u' % (idx), 'u32', vppstat['/if/tx-multicast'][:, i].sum_packets() % 2**32)
            ds.set('1.3.6.1.2.1.31.1.1.1.5.%u' % (idx), 'u32', vppstat['/if/tx-broadcast'][:, i].sum_packets() % 2**32)

            ds.set('1.3.6.1.2.1.31.1.1.1.6.%u' % (idx), 'u64', vppstat['/if/rx'][:, i].sum_octets())
            ds.set('1.3.6.1.2.1.31.1.1.1.7.%u' % (idx), 'u64', vppstat['/if/rx'][:, i].sum_packets())
            ds.set('1.3.6.1.2.1.31.1.1.1.8.%u' % (idx), 'u64', vppstat['/if/rx-multicast'][:, i].sum_packets())
            ds.set('1.3.6.1.2.1.31.1.1.1.9.%u' % (idx), 'u64', vppstat['/if/rx-broadcast'][:, i].sum_packets())

            ds.set('1.3.6.1.2.1.31.1.1.1.10.%u' % (idx), 'u64', vppstat['/if/tx'][:, i].sum_octets())
            ds.set('1.3.6.1.2.1.31.1.1.1.11.%u' % (idx), 'u64', vppstat['/if/tx'][:, i].sum_packets())
            ds.set('1.3.6.1.2.1.31.1.1.1.12.%u' % (idx), 'u64', vppstat['/if/tx-multicast'][:, i].sum_packets())
            ds.set('1.3.6.1.2.1.31.1.1.1.13.%u' % (idx), 'u64', vppstat['/if/tx-broadcast'][:, i].sum_packets())

            speed = 0
            if ifname.startswith("loop") or ifname.startswith("tap"):
                speed = 1000
            elif not ifname in ifaces:
                self.logger.warning("Could not get link speed for interface %s", ifname)
            else:
                speed = int(ifaces[ifname].link_speed / 1000)
            ds.set('1.3.6.1.2.1.31.1.1.1.15.%u' % (idx), 'gauge32', speed)

            ds.set('1.3.6.1.2.1.31.1.1.1.16.%u' % (idx), 'int', 2)   # Hardcode to false(2)
            ds.set('1.3.6.1.2.1.31.1.1.1.17.%u' % (idx), 'int', 1)   # Hardcode to true(1)

            if self.config and not ifAlias:
                try:
                    descr = get_description_by_ifname(self.config, ifname)
                    if descr:
                        self.logger.debug("Setting ifAlias of %s to config description '%s'" % (ifname, descr))
                        ifAlias = descr
                except:
                    pass
            if not ifAlias:
                self.logger.debug("Setting ifAlias of %s to ifname %s" % (ifname, ifname))
                ifAlias = ifname
            ds.set('1.3.6.1.2.1.31.1.1.1.18.%u' % (idx), 'str', ifAlias)
            ds.set('1.3.6.1.2.1.31.1.1.1.19.%u' % (idx), 'ticks', 0)  # Hardcode to Timeticks: (0) 0:00:00.00
        return ds

def main():
    global args

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', dest='address', default="localhost:705", type=str, help="""Location of the SNMPd agent (unix-path or host:port), default localhost:705""")
    parser.add_argument('-p', dest='period', type=int, default=30, help="""Period to poll VPP, default 30 (seconds)""")
    parser.add_argument('-c', dest='config', type=str, help="""Optional vppcfg YAML configuration file, default empty""")
    parser.add_argument('-d', dest='debug', action='store_true', help="""Enable debug, default False""")

    args = parser.parse_args()
    if args.debug:
        print("Arguments:", args)

    agentx.setup_logging(debug=args.debug)

    try:
        a = MyAgent(server_address=args.address, period=args.period)
        a.run()
    except Exception as e:
        print("Unhandled exception:", e)
        a.stop()
    except KeyboardInterrupt:
        a.stop()

    sys.exit(-1)

if __name__ == "__main__":
    main()
