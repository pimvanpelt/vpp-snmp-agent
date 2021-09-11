#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vppstats import VPPStats
from vppapi import VPPApi
import agentx

class MyAgent(agentx.Agent):
    def setup(self):
        global vppstat, vpp, logger

        self.logger.info("Connecting to VPP Stats...")
        vppstat = VPPStats(socketname='/run/vpp/stats.sock', timeout=2)
        if not vppstat.connect():
            self.logger.error("Can't connect to VPP Stats API, bailing")
            return False

        vpp = VPPApi(clientname='vpp-snmp-agent')
        if not vpp.connect():
            logger.error("Can't connect to VPP API, bailing")
            return False

        self.register('1.3.6.1.2.1.2.2.1')
        self.register('1.3.6.1.2.1.31.1.1.1')

        return True


    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ds = agentx.DataSet()
        ifaces = vpp.get_ifaces()
        self.logger.debug("%d VPP interfaces retrieved" % len(ifaces))
        self.logger.debug("%d VPP Stats interfaces retrieved" % len(vppstat['/if/names']))

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            idx = 1000+i

            ds.set('1.3.6.1.2.1.2.2.1.1.%u' % (idx), 'int', idx)
            ds.set('1.3.6.1.2.1.2.2.1.2.%u' % (idx), 'str', ifname)

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
                if int(ifaces[ifname].flags) & 2:
                    admin_status = 1  # up
                else:
                    admin_status = 2  # down
            ds.set('1.3.6.1.2.1.2.2.1.7.%u' % (idx), 'int', admin_status)

            oper_status = 3  # testing
            if not ifname in ifaces:
                self.logger.warning("Could not get OperStatus for interface %s", ifname)
            else:
                if int(ifaces[ifname].flags) & 1:
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

            ds.set('1.3.6.1.2.1.31.1.1.1.1.%u' % (idx), 'str', ifname)
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
            ds.set('1.3.6.1.2.1.31.1.1.1.18.%u' % (idx), 'str', ifname)
            ds.set('1.3.6.1.2.1.31.1.1.1.19.%u' % (idx), 'ticks', 0)  # Hardcode to Timeticks: (0) 0:00:00.00
        return ds

def main():
    agentx.setup_logging(debug=False)

    try:
        a = MyAgent(server_address='/run/vpp/agentx.sock')
        a.run()
    except Exception as e:
        print("Unhandled exception:", e)
        a.stop()
    except KeyboardInterrupt:
        a.stop()

if __name__ == "__main__":
    main()
