#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vppstats import VPPStats
from vppapi import VPPApi
import time
import pyagentx
import logging
import threading


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger('pyagentx.vppstats')
logger.addHandler(NullHandler())


class ifName(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_OCTETSTRING(str(i + 1), vppstat['/if/names'][i])


class ifIndex(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_INTEGER(str(i + 1), i + 1)


class ifType(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            t = 6  # ethermet-csmacd
            if vppstat['/if/names'][i].startswith("loop"):
                t = 24  # softwareLoopback
            self.set_INTEGER(str(i + 1), t)


class ifMtu(pyagentx.Updater):
    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ifaces = vpp.get_ifaces()

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            mtu = 0
            if not ifname in ifaces:
                logger.warning("Could not get MTU for interface %s", ifname)
            else:
                mtu = ifaces[ifname].mtu[0]
            self.set_INTEGER(str(i + 1), mtu)


class ifSpeed(pyagentx.Updater):
    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ifaces = vpp.get_ifaces()

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            speed = 0
            if ifname.startswith("loop") or ifname.startswith("tap"):
                speed = 1000000000
            elif not ifname in ifaces:
                logger.warning("Could not get link speed for interface %s",
                               ifname)
            else:
                speed = ifaces[ifname].link_speed * 1000
            if speed >= 2**32:
                speed = 2**32 - 1
            self.set_GAUGE32(str(i + 1), speed)


class ifAdminStatus(pyagentx.Updater):
    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ifaces = vpp.get_ifaces()

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            state = 3  # testing
            if not ifname in ifaces:
                logger.warning("Could not get AdminStatus for interface %s",
                               ifname)
            else:
                if int(ifaces[ifname].flags) & 2:
                    state = 1  # up
                else:
                    state = 2  # down
            self.set_INTEGER(str(i + 1), state)


class ifOperStatus(pyagentx.Updater):
    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ifaces = vpp.get_ifaces()

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            state = 3  # testing
            if not ifname in ifaces:
                logger.warning("Could not get OperStatus for interface %s",
                               ifname)
            else:
                if int(ifaces[ifname].flags) & 1:
                    state = 1  # up
                else:
                    state = 2  # down
            self.set_INTEGER(str(i + 1), state)


class ifPhysAddress(pyagentx.Updater):
    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ifaces = vpp.get_ifaces()

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            mac = "00:00:00:00:00:00"
            if not ifname in ifaces:
                logger.warning("Could not get PhysAddress for interface %s",
                               ifname)
            else:
                mac = str(ifaces[ifname].l2_address)
            self.set_OCTETSTRING(str(i + 1), mac)


class ifAlias(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_OCTETSTRING(str(i + 1), vppstat['/if/names'][i])


class ifInMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(
                str(i + 1),
                vppstat['/if/rx-multicast'][:, i].sum_packets() % 2**32)


class ifInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(
                str(i + 1),
                vppstat['/if/rx-broadcast'][:, i].sum_packets() % 2**32)


class ifOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(
                str(i + 1),
                vppstat['/if/tx-multicast'][:, i].sum_packets() % 2**32)


class ifOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(
                str(i + 1),
                vppstat['/if/tx-broadcast'][:, i].sum_packets() % 2**32)


class ifHCInOctets(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/rx'][:,
                                                             i].sum_octets())


class ifHCInUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/rx'][:,
                                                             i].sum_packets())


class ifHCInMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/rx-multicast'][:, i].sum_packets())


class ifHCInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/rx-broadcast'][:, i].sum_packets())


class ifHCOutOctets(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/tx'][:,
                                                             i].sum_octets())


class ifHCOutUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/tx'][:,
                                                             i].sum_packets())


class ifHCOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/tx-multicast'][:, i].sum_packets())


class ifHCOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/tx-broadcast'][:, i].sum_packets())


class ifHighSpeed(pyagentx.Updater):
    def update(self):
        global vppstat, vpp
        vppstat.connect()
        vpp.connect()

        ifaces = vpp.get_ifaces()

        for i in range(len(vppstat['/if/names'])):
            ifname = vppstat['/if/names'][i]
            speed = 0
            if ifname.startswith("loop") or ifname.startswith("tap"):
                speed = 1000
            elif not ifname in ifaces:
                logger.warning("Could not get link speed for interface %s",
                               ifname)
            else:
                speed = int(ifaces[ifname].link_speed / 1000)
            self.set_GAUGE32(str(i + 1), speed)


class ifPromiscuousMode(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            # Hardcode to false(2)
            self.set_INTEGER(str(i + 1), 2)


class ifConnectorPresent(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            # Hardcode to true(1)
            self.set_INTEGER(str(i + 1), 1)


class ifCounterDiscontinuityTime(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            # Hardcode to Timeticks: (0) 0:00:00.00
            self.set_TIMETICKS(str(i + 1), 0)


class ifInOctets(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx'][:, i].sum_octets() % 2**32)


class ifInUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx'][:, i].sum_packets() % 2**32)


class ifInNUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(
                str(i + 1),
                vppstat['/if/rx-multicast'][:, i].sum_packets() % 2**32)


class ifInDiscards(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-no-buf'][:, i].sum() % 2**32)


class ifInErrors(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-error'][:, i].sum() % 2**32)


class ifOutOctets(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx'][:, i].sum_octets() % 2**32)


class ifOutUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx'][:, i].sum_packets() % 2**32)


class ifOutNUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(
                str(i + 1),
                vppstat['/if/tx-multicast'][:, i].sum_packets() % 2**32)


class ifOutDiscards(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/drops'][:, i].sum() % 2**32)


class ifOutErrors(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx-error'][:, i].sum() % 2**32)


class MyAgent(pyagentx.Agent):
    def setup(self):

        # iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry
        self.register('1.3.6.1.2.1.2.2.1.1', ifIndex)
        self.register('1.3.6.1.2.1.2.2.1.2', ifName)
        self.register('1.3.6.1.2.1.2.2.1.3', ifType)
        self.register('1.3.6.1.2.1.2.2.1.4', ifMtu)
        self.register('1.3.6.1.2.1.2.2.1.5', ifSpeed)
        self.register('1.3.6.1.2.1.2.2.1.6', ifPhysAddress)
        self.register('1.3.6.1.2.1.2.2.1.7', ifAdminStatus)
        self.register('1.3.6.1.2.1.2.2.1.8', ifOperStatus)
        self.register('1.3.6.1.2.1.2.2.1.9', ifCounterDiscontinuityTime)
        self.register('1.3.6.1.2.1.2.2.1.10', ifInOctets)
        self.register('1.3.6.1.2.1.2.2.1.11', ifInUcastPkts)
        self.register('1.3.6.1.2.1.2.2.1.12', ifInNUcastPkts)
        self.register('1.3.6.1.2.1.2.2.1.13', ifInDiscards)
        self.register('1.3.6.1.2.1.2.2.1.14', ifInErrors)

        self.register('1.3.6.1.2.1.2.2.1.16', ifOutOctets)
        self.register('1.3.6.1.2.1.2.2.1.17', ifOutUcastPkts)
        self.register('1.3.6.1.2.1.2.2.1.18', ifOutNUcastPkts)
        self.register('1.3.6.1.2.1.2.2.1.19', ifOutDiscards)
        self.register('1.3.6.1.2.1.2.2.1.20', ifOutErrors)

        # iso.org.dod.internet.mgmt.mib_2.ifMIB.ifMIBObjects.ifXTable.ifXEntry
        self.register('1.3.6.1.2.1.31.1.1.1.1', ifName)
        self.register('1.3.6.1.2.1.31.1.1.1.2', ifInMulticastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.3', ifInBroadcastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.4', ifOutMulticastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.5', ifOutBroadcastPkts)

        self.register('1.3.6.1.2.1.31.1.1.1.6', ifHCInOctets)
        self.register('1.3.6.1.2.1.31.1.1.1.7', ifHCInUcastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.8', ifHCInMulticastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.9', ifHCInBroadcastPkts)

        self.register('1.3.6.1.2.1.31.1.1.1.10', ifHCOutOctets)
        self.register('1.3.6.1.2.1.31.1.1.1.11', ifHCOutUcastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.12', ifHCOutMulticastPkts)
        self.register('1.3.6.1.2.1.31.1.1.1.13', ifHCOutBroadcastPkts)

        self.register('1.3.6.1.2.1.31.1.1.1.15', ifHighSpeed)
        self.register('1.3.6.1.2.1.31.1.1.1.16', ifPromiscuousMode)
        self.register('1.3.6.1.2.1.31.1.1.1.17', ifConnectorPresent)
        self.register('1.3.6.1.2.1.31.1.1.1.18', ifAlias)
        self.register('1.3.6.1.2.1.31.1.1.1.19', ifCounterDiscontinuityTime)


def main():
    global vppstat, vpp, logger

    pyagentx.setup_logging(debug=False)

    vppstat = VPPStats(socketname='/run/vpp/stats.sock', timeout=2)
    vppstat.connect()

    vpp = VPPApi()
    if not vpp.connect():
        logger.error("Can't connect to VPP API, bailing")
        return

    try:
        a = MyAgent()
        a.start()
    except Exception as e:
        print("Unhandled exception:", e)
        a.stop()
    except KeyboardInterrupt:
        a.stop()

    vppstat.disconnect()
    vpp.disconnect()


if __name__ == "__main__":
    main()
