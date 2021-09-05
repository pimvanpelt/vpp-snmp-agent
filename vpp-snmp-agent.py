#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vppstats import VPPStats
import time
import pyagentx
import logging
import threading


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger('pyagentx.vpp')
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
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-multicast'][:, i].sum_packets())


class ifInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-broadcast'][:, i].sum_packets())


class ifOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx-multicast'][:, i].sum_packets())


class ifOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx-broadcast'][:, i].sum_packets())


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
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_GAUGE32(str(i + 1), 1000)


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
            self.set_COUNTER32(str(i + 1), vppstat['/if/rx'][:,
                                                             i].sum_octets())


class ifInUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/rx'][:,
                                                             i].sum_packets())


class ifInNUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-multicast'][:, i].sum_packets())


class ifInDiscards(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/rx-no-buf'][:,
                                                                    i].sum())


class ifInErrors(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/rx-error'][:, i].sum())


class ifOutOctets(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/tx'][:,
                                                             i].sum_octets())


class ifOutUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/tx'][:,
                                                             i].sum_packets())


class ifOutNUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx-multicast'][:, i].sum_packets())


class ifOutDiscards(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/drops'][:, i].sum())


class ifOutErrors(pyagentx.Updater):
    def update(self):
        global vppstat
        vppstat.connect()

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1), vppstat['/if/tx-error'][:, i].sum())


class MyAgent(pyagentx.Agent):
    def setup(self):

        # iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry
        self.register('1.3.6.1.2.1.2.2.1.1', ifIndex)
        self.register('1.3.6.1.2.1.2.2.1.2', ifName)
        self.register('1.3.6.1.2.1.2.2.1.3', ifType)
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

        # TODO(pim) -- these require VPP API calls
        #4 .iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifMtu.132 = INTEGER: 1500
        #5 .iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifSpeed.132 = Gauge32: 10000000
        #6 .iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifPhysAddress.132 = Hex-STRING: 68 05 CA 32 46 15
        #7 .iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifAdminStatus.132 = INTEGER: 1
        #8 .iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifOperStatus.132 = INTEGER: 1

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
    global vppstat

    pyagentx.setup_logging(debug=False)

    vppstat = VPPStats(socketname='/run/vpp/stats.sock', timeout=2)
    vppstat.connect()

    try:
        a = MyAgent()
        a.start()
    except Exception as e:
        print("Unhandled exception:", e)
        a.stop()
    except KeyboardInterrupt:
        a.stop()

    vppstat.disconnect()


if __name__ == "__main__":
    main()
