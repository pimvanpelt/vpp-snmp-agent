#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vppstats import VPPStats
import time
import pyagentx
import logging
import threading

vppstat_lastread = 0
vppstat_ifstat = {
    'ifNames': [],
    'ifHCInOctets': [],
    'ifHCInUcastPkts': [],
    'ifHCInMulticastPkts': [],
    'ifHCInBroadcastPkts': [],
    'ifHCOutOctets': [],
    'ifHCOutUcastPkts': [],
    'ifHCOutMulticastPkts': [],
    'ifHCOutBroadcastPkts': [],
    'ifHighSpeed': []
}

vppstat_lock = threading.Lock()


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger('pyagentx.vpp')
logger.addHandler(NullHandler())


def vppstat_update():
    global vppstat_lastread, vppstat_lock, vppstat_ifstat, logger

    vppstat_lock.acquire()
    try:
        if time.time() - vppstat_lastread < 9.0:
            logger.debug("Skipping, cache still fresh")
            vppstat_lock.release()
            return

        logger.info("Fetching interface data from VPP")
        vppstat = VPPStats(socketname='/run/vpp/stats.sock', timeout=2)
        vppstat.connect()
        vppstat_ifstat['ifNames'] = vppstat['/if/names']
        vppstat_ifstat['ifHCInOctets'].clear()
        vppstat_ifstat['ifHCInUcastPkts'].clear()
        vppstat_ifstat['ifHCInMulticastPkts'].clear()
        vppstat_ifstat['ifHCInBroadcastPkts'].clear()
        vppstat_ifstat['ifHCOutOctets'].clear()
        vppstat_ifstat['ifHCOutUcastPkts'].clear()
        vppstat_ifstat['ifHCOutMulticastPkts'].clear()
        vppstat_ifstat['ifHCOutBroadcastPkts'].clear()
        vppstat_ifstat['ifHighSpeed'].clear()

        for i in range(len(vppstat_ifstat['ifNames'])):
            vppstat_ifstat['ifHCInOctets'].append(
                vppstat['/if/rx'][:, i].sum_octets())
            vppstat_ifstat['ifHCInUcastPkts'].append(
                vppstat['/if/rx'][:, i].sum_packets())
            vppstat_ifstat['ifHCInMulticastPkts'].append(
                vppstat['/if/rx-multicast'][:, i].sum_packets())
            vppstat_ifstat['ifHCInBroadcastPkts'].append(
                vppstat['/if/rx-broadcast'][:, i].sum_packets())

            vppstat_ifstat['ifHCOutOctets'].append(
                vppstat['/if/tx'][:, i].sum_octets())
            vppstat_ifstat['ifHCOutUcastPkts'].append(
                vppstat['/if/tx'][:, i].sum_packets())
            vppstat_ifstat['ifHCOutMulticastPkts'].append(
                vppstat['/if/tx-multicast'][:, i].sum_packets())
            vppstat_ifstat['ifHCOutBroadcastPkts'].append(
                vppstat['/if/tx-broadcast'][:, i].sum_packets())

            # TODO(pim) retrieve from vpp_papi
            # IF-MIB::ifHighSpeed.2 = Gauge32: 1000
            vppstat_ifstat['ifHighSpeed'].append(1000)


# TODO(pim) retrieve from linux namespace if present
# IF-MIB::ifAlias.2 = STRING: Infra: nikhef-core-1.nl.switch.coloclue.net e1/34

# Initializing these to defaults:
# IF-MIB::ifPromiscuousMode.2 = INTEGER: false(2)
# IF-MIB::ifConnectorPresent.2 = INTEGER: true(1)
# IF-MIB::ifCounterDiscontinuityTime.2 = Timeticks: (0) 0:00:00.00

        logger.info("Fetched data for %u interfaces" %
                    len(vppstat_ifstat['ifNames']))
        vppstat_lastread = time.time()
        vppstat.disconnect()
    except Exception as e:
        logger.error("Error occured, releasing lock: ", e)
    vppstat_lock.release()
    return


class ifName(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_OCTETSTRING(str(i + 1), vppstat_ifstat['ifNames'][i])


class ifAlias(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_OCTETSTRING(str(i + 1), vppstat_ifstat['ifNames'][i])


class ifInMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat_ifstat['ifHCInMulticastPkts'][i])


class ifInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat_ifstat['ifHCInBroadcastPkts'][i])


class ifOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat_ifstat['ifHCOutMulticastPkts'][i])


class ifOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER32(str(i + 1),
                               vppstat_ifstat['ifHCOutBroadcastPkts'][i])


class ifHCInOctets(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1), vppstat_ifstat['ifHCInOctets'][i])


class ifHCInUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat_ifstat['ifHCInUcastPkts'][i])


class ifHCInMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat_ifstat['ifHCInMulticastPkts'][i])


class ifHCInBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat_ifstat['ifHCInBroadcastPkts'][i])


class ifHCOutOctets(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1), vppstat_ifstat['ifHCOutOctets'][i])


class ifHCOutUcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat_ifstat['ifHCOutUcastPkts'][i])


class ifHCOutMulticastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat_ifstat['ifHCOutMulticastPkts'][i])


class ifHCOutBroadcastPkts(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_COUNTER64(str(i + 1),
                               vppstat_ifstat['ifHCOutBroadcastPkts'][i])


class ifHighSpeed(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            self.set_GAUGE32(str(i + 1), vppstat_ifstat['ifHighSpeed'][i])


class ifPromiscuousMode(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            # Hardcode to false(2)
            self.set_INTEGER(str(i + 1), 2)


class ifConnectorPresent(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
            # Hardcode to true(1)
            self.set_INTEGER(str(i + 1), 1)


class ifCounterDiscontinuityTime(pyagentx.Updater):
    def update(self):
        global vppstat_ifstat

        vppstat_update()
        for i in range(len(vppstat_ifstat['ifNames'])):
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
    pyagentx.setup_logging()

    try:
        a = MyAgent()
        a.start()
    except Exception as e:
        print("Unhandled exception:", e)
        a.stop()
    except KeyboardInterrupt:
        a.stop()


if __name__ == "__main__":
    main()
