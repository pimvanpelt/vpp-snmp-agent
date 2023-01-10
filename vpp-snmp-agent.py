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
        for k, v in ifaces.items():
            if v.sw_if_index == sw_if_index:
                return v
    except:
        pass
    return None


def get_lcp_by_host_sw_if_index(lcp, host_sw_if_index):
    try:
        for k, v in lcp.items():
            if v.host_sw_if_index == host_sw_if_index:
                return v
    except:
        pass
    return None


def get_description_by_ifname(config, name):
    try:
        if "interfaces" in config:
            for ifname, iface in config["interfaces"].items():
                if ifname == name:
                    return iface["description"]
                if "sub-interfaces" in iface:
                    for sub_id, sub_iface in iface["sub-interfaces"].items():
                        sub_ifname = "%s.%d" % (ifname, sub_id)
                        if name == sub_ifname:
                            return sub_iface["description"]
        if "loopbacks" in config:
            for ifname, iface in config["loopbacks"].items():
                if ifname == name:
                    return iface["description"]
        if "taps" in config:
            for ifname, iface in config["taps"].items():
                if ifname == name:
                    return iface["description"]
        if "vxlan_tunnels" in config:
            for ifname, iface in config["vxlan_tunnels"].items():
                if ifname == name:
                    return iface["description"]
    except:
        pass
    return None


class MyAgent(agentx.Agent):
    def setup(self):
        self.config = None
        if self._args.config:
            try:
                with open(self._args.config, "r") as f:
                    self.logger.info("Loading configfile %s" % self._args.config)
                    self.config = yaml.load(f, Loader=yaml.FullLoader)
                    self.logger.debug("Config: %s" % self.config)
            except:
                self.logger.error("Couldn't read config from %s" % self._args.config)

        try:
            self.logger.info("Connecting to VPP Stats Segment")
            self.vppstat = VPPStats(socketname="/run/vpp/stats.sock", timeout=2)
            self.vppstat.connect()
        except:
            self.logger.error("Could not connect to VPPStats segment")
            return False

        try:
            self.vpp = VPPApi(clientname="vpp-snmp-agent")
            self.vpp.connect()
        except:
            self.logger.error("Could not connect to VPP API")
            return False

        self.register("1.3.6.1.2.1.2.2.1")
        self.register("1.3.6.1.2.1.31.1.1.1")

        return True

    def update(self):
        try:
            self.vpp.connect()
            r = self.vpp.vpp.api.control_ping()
            self.logger.debug(f"VPP API: {r}")
            self.vppstat.connect()
        except Exception as e:
            self.logger.error(f"VPP API: {e}, retrying")
            self.vppstat.disconnect()
            self.vpp.disconnect()
            return False

        ds = agentx.DataSet()
        ifaces = self.vpp.get_ifaces()
        lcp = self.vpp.get_lcp()

        num_ifaces = len(ifaces)
        num_vppstat = len(self.vppstat["/if/names"])
        num_lcp = len(lcp)
        self.logger.debug(
            "Retrieved Interfaces: vppapi=%d vppstat=%d lcp=%d"
            % (num_ifaces, num_vppstat, num_lcp)
        )

        if num_ifaces != num_vppstat:
            self.logger.warning(
                "Interfaces count mismatch: vppapi=%d vppstat=%d"
                % (num_ifaces, num_vppstat)
            )

        for i in range(len(self.vppstat["/if/names"])):
            ifname = self.vppstat["/if/names"][i]
            idx = 1000 + i

            ds.set("1.3.6.1.2.1.2.2.1.1.%u" % (idx), "int", idx)

            ifName = ifname
            ifAlias = None
            try:
                if self.config and ifname.startswith("tap"):
                    host_sw_if_index = ifaces[ifname].sw_if_index
                    lip = get_lcp_by_host_sw_if_index(lcp, host_sw_if_index)
                    if lip:
                        phy = get_phy_by_sw_if_index(ifaces, lip.phy_sw_if_index)
                        ifName = lip.host_if_name
                        self.logger.debug(
                            "Setting ifName of %s to '%s'" % (ifname, ifName)
                        )
                        if phy:
                            ifAlias = "LCP %s (%s)" % (phy.interface_name, ifname)
                            self.logger.debug(
                                "Setting ifAlias of %s to '%s'" % (ifname, ifAlias)
                            )
            except:
                self.logger.debug("No config entry found for ifname %s" % (ifname))
                pass

            ds.set("1.3.6.1.2.1.2.2.1.2.%u" % (idx), "str", ifName)

            if ifname.startswith("loop"):
                ds.set("1.3.6.1.2.1.2.2.1.3.%u" % (idx), "int", 24)  # softwareLoopback
            else:
                ds.set("1.3.6.1.2.1.2.2.1.3.%u" % (idx), "int", 6)  # ethermet-csmacd

            mtu = 0
            if not ifname in ifaces:
                self.logger.warning("Could not get MTU for interface %s", ifname)
            else:
                mtu = ifaces[ifname].mtu[0]
            ds.set("1.3.6.1.2.1.2.2.1.4.%u" % (idx), "int", mtu)

            speed = 0
            if ifname.startswith("loop") or ifname.startswith("tap"):
                speed = 1000000000
            elif not ifname in ifaces:
                self.logger.warning("Could not get link speed for interface %s", ifname)
            else:
                speed = ifaces[ifname].link_speed * 1000
            if speed >= 2 ** 32:
                speed = 2 ** 32 - 1
            ds.set("1.3.6.1.2.1.2.2.1.5.%u" % (idx), "gauge32", speed)

            mac = "00:00:00:00:00:00"
            if not ifname in ifaces:
                self.logger.warning(
                    "Could not get PhysAddress for interface %s", ifname
                )
            else:
                mac = str(ifaces[ifname].l2_address)
            ds.set("1.3.6.1.2.1.2.2.1.6.%u" % (idx), "str", mac)

            admin_status = 3  # testing
            if not ifname in ifaces:
                self.logger.warning(
                    "Could not get AdminStatus for interface %s", ifname
                )
            else:
                if int(ifaces[ifname].flags) & 1:
                    admin_status = 1  # up
                else:
                    admin_status = 2  # down
            ds.set("1.3.6.1.2.1.2.2.1.7.%u" % (idx), "int", admin_status)

            oper_status = 3  # testing
            if not ifname in ifaces:
                self.logger.warning("Could not get OperStatus for interface %s", ifname)
            else:
                if int(ifaces[ifname].flags) & 2:
                    oper_status = 1  # up
                else:
                    oper_status = 2  # down
            ds.set("1.3.6.1.2.1.2.2.1.8.%u" % (idx), "int", oper_status)

            ds.set("1.3.6.1.2.1.2.2.1.9.%u" % (idx), "ticks", 0)
            ds.set(
                "1.3.6.1.2.1.2.2.1.10.%u" % (idx),
                "u32",
                self.vppstat["/if/rx"][:, i].sum_octets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.11.%u" % (idx),
                "u32",
                self.vppstat["/if/rx"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.12.%u" % (idx),
                "u32",
                self.vppstat["/if/rx-multicast"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.13.%u" % (idx),
                "u32",
                self.vppstat["/if/rx-no-buf"][:, i].sum() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.14.%u" % (idx),
                "u32",
                self.vppstat["/if/rx-error"][:, i].sum() % 2 ** 32,
            )

            ds.set(
                "1.3.6.1.2.1.2.2.1.16.%u" % (idx),
                "u32",
                self.vppstat["/if/tx"][:, i].sum_octets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.17.%u" % (idx),
                "u32",
                self.vppstat["/if/tx"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.18.%u" % (idx),
                "u32",
                self.vppstat["/if/tx-multicast"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.19.%u" % (idx),
                "u32",
                self.vppstat["/if/drops"][:, i].sum() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.2.2.1.20.%u" % (idx),
                "u32",
                self.vppstat["/if/tx-error"][:, i].sum() % 2 ** 32,
            )

            ds.set("1.3.6.1.2.1.31.1.1.1.1.%u" % (idx), "str", ifName)
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.2.%u" % (idx),
                "u32",
                self.vppstat["/if/rx-multicast"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.3.%u" % (idx),
                "u32",
                self.vppstat["/if/rx-broadcast"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.4.%u" % (idx),
                "u32",
                self.vppstat["/if/tx-multicast"][:, i].sum_packets() % 2 ** 32,
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.5.%u" % (idx),
                "u32",
                self.vppstat["/if/tx-broadcast"][:, i].sum_packets() % 2 ** 32,
            )

            ds.set(
                "1.3.6.1.2.1.31.1.1.1.6.%u" % (idx),
                "u64",
                self.vppstat["/if/rx"][:, i].sum_octets(),
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.7.%u" % (idx),
                "u64",
                self.vppstat["/if/rx"][:, i].sum_packets(),
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.8.%u" % (idx),
                "u64",
                self.vppstat["/if/rx-multicast"][:, i].sum_packets(),
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.9.%u" % (idx),
                "u64",
                self.vppstat["/if/rx-broadcast"][:, i].sum_packets(),
            )

            ds.set(
                "1.3.6.1.2.1.31.1.1.1.10.%u" % (idx),
                "u64",
                self.vppstat["/if/tx"][:, i].sum_octets(),
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.11.%u" % (idx),
                "u64",
                self.vppstat["/if/tx"][:, i].sum_packets(),
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.12.%u" % (idx),
                "u64",
                self.vppstat["/if/tx-multicast"][:, i].sum_packets(),
            )
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.13.%u" % (idx),
                "u64",
                self.vppstat["/if/tx-broadcast"][:, i].sum_packets(),
            )

            speed = 0
            if ifname.startswith("loop") or ifname.startswith("tap"):
                speed = 1000
            elif not ifname in ifaces:
                self.logger.warning("Could not get link speed for interface %s", ifname)
            else:
                speed = int(ifaces[ifname].link_speed / 1000)
            ds.set("1.3.6.1.2.1.31.1.1.1.15.%u" % (idx), "gauge32", speed)

            ds.set(
                "1.3.6.1.2.1.31.1.1.1.16.%u" % (idx), "int", 2
            )  # Hardcode to false(2)
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.17.%u" % (idx), "int", 1
            )  # Hardcode to true(1)

            if self.config and not ifAlias:
                try:
                    descr = get_description_by_ifname(self.config, ifname)
                    if descr:
                        self.logger.debug(
                            "Setting ifAlias of %s to config description '%s'"
                            % (ifname, descr)
                        )
                        ifAlias = descr
                except:
                    pass
            if not ifAlias:
                self.logger.debug(
                    "Setting ifAlias of %s to ifname %s" % (ifname, ifname)
                )
                ifAlias = ifname
            ds.set("1.3.6.1.2.1.31.1.1.1.18.%u" % (idx), "str", ifAlias)
            ds.set(
                "1.3.6.1.2.1.31.1.1.1.19.%u" % (idx), "ticks", 0
            )  # Hardcode to Timeticks: (0) 0:00:00.00
        return ds


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-a",
        dest="address",
        default="localhost:705",
        type=str,
        help="""Location of the SNMPd agent (unix-path or host:port), default localhost:705""",
    )
    parser.add_argument(
        "-p",
        dest="period",
        type=int,
        default=30,
        help="""Period to poll VPP, default 30 (seconds)""",
    )
    parser.add_argument(
        "-c",
        dest="config",
        type=str,
        help="""Optional vppcfg YAML configuration file, default empty""",
    )
    parser.add_argument(
        "-d", dest="debug", action="store_true", help="""Enable debug, default False"""
    )

    args = parser.parse_args()
    if args.debug:
        print("Arguments:", args)

    agentx.setup_logging(debug=args.debug)

    try:
        a = MyAgent(server_address=args.address, period=args.period, args=args)
        a.run()
    except Exception as e:
        print("Unhandled exception:", e)
        a.stop()
    except KeyboardInterrupt:
        a.stop()

    sys.exit(-1)


if __name__ == "__main__":
    main()
