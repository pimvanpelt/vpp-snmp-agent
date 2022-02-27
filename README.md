# VPP's Interface AgentX

This is an SNMP agent that implements the [Agentx](https://datatracker.ietf.org/doc/html/rfc2257)
protocol. It connects to VPP's `statseg` (statistics memory segment) by MMAPing
it, so the user running the agent must have read access to `/run/vpp/stats.sock`.
It also connects to VPP's API endpoint, so the user running the agent must
have read/write access to `/run/vpp/api.sock`. Both of these are typically accomplished
by running the agent as group `vpp`.

The agent connects to SNMP's `agentx` socket, which can be either a TCP socket
(by default `localhost:705`), or a unix domain socket (by default `/var/agentx/master`)
the latter being readable only by root. It's preferable to run as unprivileged user,
so a TCP socket is preferred (and the default).

The agent incorporates a refactored/modified [pyagentx](https://github.com/hosthvo/pyagentx).
The upstream pyagentx code uses a threadpool and message queue, but it was not very stable.
Often, due to lack of proper locking, updaters would overwrite parts of the MIB and as a
result, any reads that were ongoing would abruptly be truncated. I refactored the code to
be single-threaded, greatly simplifying the design (and eliminating the need for locking).

To respect the original authors, this code is released with the same BSD 2-clause license.

## Building

Install `pyinstaller` to build a binary distribution

```
sudo pip install pyinstaller
pyinstaller vpp-snmp-agent.py  --onefile

## Run it on console
dist/vpp-snmp-agent -h
usage: vpp-snmp-agent [-h] [-a ADDRESS] [-p PERIOD] [-d]

optional arguments:
  -h, --help  show this help message and exit
  -a ADDRESS  Location of the SNMPd agent (unix-path or host:port), default localhost:705
  -p PERIOD   Period to poll VPP, default 30 (seconds)
  -c CONFIG   Optional YAML configuration file, default empty
  -d          Enable debug, default False

## Install
sudo cp dist/vpp-snmp-agent /usr/sbin/
```

## Configuration file

A simple convenience configfile can provide a mapping between VPP interface names, Linux Control Plane
interface names, and descriptions. An example:

```
interfaces:
  "TenGigabitEthernet6/0/0":
    description: "Infra: xsw0.chrma0:2"
    lcp: "xe1-0"
  "TenGigabitEthernet6/0/0.3102":
    description: "Infra: QinQ to L2 Provider"
    lcp: "xe1-0.3102"
  "TenGigabitEthernet6/0/0.310211":
    description: "Cust: Customer IP Transit"
    lcp: "xe1-0.3102.11"
```

This configuration file is completely optional. If the `-c` flag is empty, or it's set but the file does
not exist, the Agent will simply enumerate all interfaces, and set the `ifAlias` OID to the same value as
the `ifName`. However, if the config file is read, it will change the behavior as follows:

*  Any `tapNN` interface names from VPP will be matched to their PHY by looking up their Linux Control Plane
   interface. The `ifName` field will be rewritten to the _LIP_ `host-if`. For example, `tap3` above will
   become `xe1-0` while `tap3.310211` will become `xe1-0.3102.11`.
*  The `ifAlias` OID for a PHY will be set to the `description` field.
*  The `ifAlias` OID for a TAP will be set to the string `LCP ` followed by its PHY `ifName`. For example,
   `xe1-0.3102.11` will become `LCP TenGigabitEthernet6/0/0.310211 (tap9)`

## SNMPd config

First, configure the snmpd to accept agentx connections by adding (at least) the following
to `snmpd.conf`:
```
master  agentx
agentXSocket tcp:localhost:705,unix:/var/agentx-dataplane/master
```

and restart snmpd to pick up the changes. Simply run `./vpp-snmp-agent.py` and it
will connect to the snmpd on localhost:705, and expose the IFMib by periodically
polling VPP. Observe the console output.


## Running in production

Meant to be run on Ubuntu, copy `*.service`, disable the main snmpd, enable
the one that runs in the dataplane network namespace and start it all up:

```
sudo cp netns-dataplane.service /usr/lib/systemd/system/
sudo cp snmpd-dataplane.service /usr/lib/systemd/system/
sudo cp vpp-snmp-agent.service /usr/lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl stop snmpd
sudo systemctl disable snmpd
sudo systemctl enable netns-dataplane
sudo systemctl start netns-dataplane
sudo systemctl enable snmpd-dataplane
sudo systemctl start snmpd-dataplane
sudo systemctl enable vpp-snmp-agent
sudo systemctl start vpp-snmp-agent
```
