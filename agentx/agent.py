#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
)

import time
import logging
import agentx
from agentx.dataset import DataSet
from agentx.network import Network

class NullHandler(logging.Handler):
    def emit(self, record):
        pass


class Agent(object):
    def __init__(self, server_address='/var/agentx/master', period=30.0):
        self.logger = logging.getLogger('agentx.agent')
        self.logger.addHandler(NullHandler())

        self._servingset = DataSet()
        self._workingset = DataSet()
        self._lastupdate = 0
        self._update_period = period  # Seconds

        self._net = Network(server_address = server_address)

        self._oid_list = []

    def _update(self):
        ds = self.update()
        self._net.update(ds._data)
        self._lastupdate = time.time()

    def run(self):
        self.logger.info('Calling setup')
        if not self.setup():
            self.logger.error('Setup failed - exiting')
            return

        self.logger.info('Initial update')
        self._update()

        while True:
            if not self._net.is_connected():
              self.logger.info('Opening AgentX connection')
              self._net.start(self._oid_list)

            if time.time() - self._lastupdate > self._update_period:
                self._update()

            try:
                self._net.run()
            except Exception as e:
                self.logger.error('An exception occurred: %s' % e)
                self.logger.error('Reconnecting')
                self._net.disconnect()
                time.sleep(0.1)

    def stop(self):
        self.logger.debug('Stopping')
        self._net.disconnect()
        pass


    def setup(self):
        # Override this
        pass


    def update(self):
        # Override this
        pass

    def register(self, oid_list):
        if not isinstance(oid_list, list):
            oid_list = [oid_list]

        for oid in oid_list:
            if not oid in self._oid_list:
                self.logger.debug('Adding %s to list' % oid)
                self._oid_list.append(oid)
