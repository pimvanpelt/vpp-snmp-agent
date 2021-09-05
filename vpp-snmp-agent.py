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

        for i in range(len(vppstat['/if/names'])):
            self.set_OCTETSTRING(str(i + 1), vppstat['/if/names'][i])


class ifAlias(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_OCTETSTRING(str(i + 1), vppstat['/if/names'][i])


class ifInMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-multicast'][:, i].sum_packets())


class ifInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/rx-broadcast'][:, i].sum_packets())


class ifOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx-multicast'][:, i].sum_packets())


class ifOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat['/if/tx-broadcast'][:, i].sum_packets())


class ifHCInOctets(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/rx'][:,
                                                             i].sum_octets())


class ifHCInUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/rx'][:,
                                                             i].sum_packets())


class ifHCInMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/rx-multicast'][:, i].sum_packets())


class ifHCInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/rx-broadcast'][:, i].sum_packets())


class ifHCOutOctets(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/tx'][:,
                                                             i].sum_octets())


class ifHCOutUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1), vppstat['/if/tx'][:,
                                                             i].sum_packets())


class ifHCOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/tx-multicast'][:, i].sum_packets())


class ifHCOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat['/if/tx-broadcast'][:, i].sum_packets())


class ifHighSpeed(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            self.set_GAUGE32(str(i + 1), 1000)


class ifPromiscuousMode(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            # Hardcode to false(2)
            self.set_INTEGER(str(i + 1), 2)


class ifConnectorPresent(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            # Hardcode to true(1)
            self.set_INTEGER(str(i + 1), 1)


class ifCounterDiscontinuityTime(pyagentx.Updater):
    def update(self):
        global vppstat

        for i in range(len(vppstat['/if/names'])):
            # Hardcode to Timeticks: (0) 0:00:00.00
            self.set_TIMETICKS(str(i + 1), 0)


class MyAgent(pyagentx.Agent):
    def setup(self):
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

    pyagentx.setup_logging()

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
