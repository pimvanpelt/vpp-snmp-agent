#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
)

import time
import agentx


class DataSetError(Exception):
    pass


class DataSet:
    def __init__(self):
        self._data = {}

    def set(self, oid, oid_type, value):
        if oid_type.startswith("int"):
            t = agentx.TYPE_INTEGER
        elif oid_type.startswith("str"):
            t = agentx.TYPE_OCTETSTRING
        elif oid_type.startswith("oid"):
            t = agentx.TYPE_OBJECTIDENTIFIER
        elif oid_type.startswith("ip"):
            t = agentx.TYPE_IPADDRESS
        elif oid_type == "counter32" or oid_type == "uint32" or oid_type == "u32":
            t = agentx.TYPE_COUNTER32
        elif oid_type == "gauge32":
            t = agentx.TYPE_GAUGE32
        elif oid_type.startswith("time") or oid_type.startswith("tick"):
            t = agentx.TYPE_TIMETICKS
        elif oid_type.startswith("opaque"):
            t = agentx.TYPE_OPAQUE
        elif oid_type == "counter64" or oid_type == "uint64" or oid_type == "u64":
            t = agentx.TYPE_COUNTER64
        else:
            raise DataSetErrror("Invalid oid_type: %s" % (oid_type))
            return

        self._data[oid] = {"name": oid, "type": t, "value": value}
