#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
)

import socket
import time
import logging
import agentx
from agentx.pdu import PDU


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger("agentx.network")
logger.addHandler(NullHandler())


class NetworkError(Exception):
    pass


class Network:
    def __init__(self, server_address="/var/agentx/master", debug=False):

        self.session_id = 0
        self.transaction_id = 0
        self.debug = debug
        # Data Related Variables
        self.data = {}
        self.data_idx = []
        self._connected = False
        self._server_address = server_address
        self._timeout = 0.1  # Seconds

    def connect(self):
        if self._connected:
            return

        try:
            if self._server_address.startswith("/"):
                self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.socket.connect(self._server_address)
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host, port = self._server_address.split(":")

                self.socket.connect((host, int(port)))
            self.socket.settimeout(self._timeout)
            self._connected = True
            logger.info("Connected to %s" % self._server_address)
        except socket.error:
            self._connected = False
            logger.error("Failed to connect to %s" % self._server_address)

    def disconnect(self):
        if not self._connected:
            return
        logger.info("Disconnecting from %s" % self._server_address)
        self.socket.close()
        self.socket = None
        self._connected = False
        return

    def update(self, newdata):
        if len(self.data) == 0:
            logger.info("Setting initial serving dataset (%d OIDs)" % len(newdata))
        else:
            logger.info("Replacing serving dataset (%d OIDs)" % len(newdata))
        del self.data
        self.data = newdata.copy()

        del self.data_idx
        self.data_idx = sorted(
            self.data.keys(), key=lambda k: tuple(int(part) for part in k.split("."))
        )

    def new_pdu(self, type):
        pdu = PDU(type)
        pdu.session_id = self.session_id
        pdu.transaction_id = self.transaction_id
        self.transaction_id += 1
        return pdu

    def response_pdu(self, org_pdu):
        pdu = PDU(agentx.AGENTX_RESPONSE_PDU)
        pdu.session_id = org_pdu.session_id
        pdu.transaction_id = org_pdu.transaction_id
        pdu.packet_id = org_pdu.packet_id
        return pdu

    def send_pdu(self, pdu):
        if self.debug:
            pdu.dump()
        self.socket.send(pdu.encode())

    def recv_pdu(self):
        buf = self.socket.recv(100000)
        if not buf:
            return None
        pdu = PDU()
        pdu.decode(buf)
        if self.debug:
            pdu.dump()
        return pdu

    # =========================================

    def _get_next_oid(self, oid, endoid):
        if oid in self.data:
            # Exact match found
            # logger.debug('get_next_oid, exact match of %s' % oid)
            idx = self.data_idx.index(oid)
            if idx == (len(self.data_idx) - 1):
                # Last Item in MIB, No match!
                return None
            return self.data_idx[idx + 1]
        else:
            # No exact match, find prefix
            # logger.debug('get_next_oid, no exact match of %s' % oid)
            slist = oid.split(".")
            elist = endoid.split(".")
            for tmp_oid in self.data_idx:
                tlist = tmp_oid.split(".")
                for i in range(len(tlist)):
                    try:
                        sok = int(slist[i]) <= int(tlist[i])
                        eok = int(elist[i]) >= int(tlist[i])
                        if not (sok and eok):
                            break
                    except IndexError:
                        pass
                if sok and eok:
                    return tmp_oid
            return None  # No match!

    def start(self, oid_list):
        self.connect()
        if not self._connected:
            return

        logger.debug("==== Open PDU ====")
        pdu = self.new_pdu(agentx.AGENTX_OPEN_PDU)
        self.send_pdu(pdu)
        pdu = self.recv_pdu()
        self.session_id = pdu.session_id

        logger.debug("==== Ping PDU ====")
        pdu = self.new_pdu(agentx.AGENTX_PING_PDU)
        self.send_pdu(pdu)
        pdu = self.recv_pdu()

        logger.debug("==== Register PDU ====")
        for oid in oid_list:
            logger.info("Registering: %s" % (oid))
            pdu = self.new_pdu(agentx.AGENTX_REGISTER_PDU)
            pdu.oid = oid
            self.send_pdu(pdu)
            pdu = self.recv_pdu()

        return

    def stop(self):
        self.disconnect()

    def is_connected(self):
        return self._connected

    def run(self, timeout=0.1):
        if not self._connected:
            raise NetworkError("Not connected")

        if timeout != self._timeout:
            self.socket.settimeout(timeout)
            self._timeout = timeout

        try:
            request = self.recv_pdu()
        except socket.timeout:
            return

        if not request:
            logger.error("Empty PDU, connection closed!")
            self.disconnect()
            raise NetworkError("Empty PDU, disconnecting")

        response = self.response_pdu(request)
        if request.type == agentx.AGENTX_GET_PDU:
            logger.debug("Received GET PDU")
            for rvalue in request.range_list:
                oid = rvalue[0]
                logger.debug("OID: %s" % (oid))
                if oid in self.data:
                    logger.debug("OID Found")
                    response.values.append(self.data[oid])
                else:
                    logger.debug("OID Not Found!")
                    response.values.append(
                        {
                            "type": agentx.TYPE_NOSUCHOBJECT,
                            "name": rvalue[0],
                            "value": 0,
                        }
                    )

        elif request.type == agentx.AGENTX_GETNEXT_PDU:
            logger.debug("Received GET_NEXT PDU")
            for rvalue in request.range_list:
                oid = self._get_next_oid(rvalue[0], rvalue[1])
                logger.debug("GET_NEXT: %s => %s" % (rvalue[0], oid))
                if oid:
                    response.values.append(self.data[oid])
                else:
                    response.values.append(
                        {
                            "type": agentx.TYPE_ENDOFMIBVIEW,
                            "name": rvalue[0],
                            "value": 0,
                        }
                    )

        else:
            logger.warn("Received unsupported PDU %d" % request.type)

        self.send_pdu(response)
