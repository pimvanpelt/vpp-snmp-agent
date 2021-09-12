# VPP's Interface AgentX

This is an SNMP agent that implements the [Agentx](https://datatracker.ietf.org/doc/html/rfc2257)
protocol. It connects to VPP's `statseg` (statistics memory segment) by MMAPing
it, so the user running the agent must have read access to `/run/vpp/stats.sock`.
It then connects to SNMP's `agentx` socket, which can be either a TCP socket
(by default localhost:705), or a unix domain socket (by default /var/agentx/master)
the latter being readable only by root. It's preferable to run as unprivileged user

The agent incorporates [pyagentx](https://github.com/hosthvo/pyagentx) with a few
changes, and is released with the BSD 2-clause license.

## Running

First, configure the snmpd to accept agentx connections by adding the following
to `snmpd.conf`:
```
master  agentx
agentXSocket tcp:localhost:705,unix:/var/agentx-dataplane/master
```

and restart snmpd to pick up the changes. Simply run `./vpp-snmp-agent.py` and it
will connect to the snmpd on localhost:705, and expose the IFMib by periodically
polling VPP. Observe the console output.

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
  -d          Enable debug, default False

## Install
sudo cp dist/vpp-snmp-agent /usr/sbin/
```

## Running in production

Meant to be run on Ubuntu, copy `vpp-snmp-agent.service`, enable and start:

```
sudo cp snmpd-dataplane.service /usr/lib/systemd/system/
sudo cp vpp-snmp-agent.service /usr/lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable snmpd-dataplane
sudo systemctl start snmpd-dataplane
sudo systemctl enable vpp-snmp-agent
sudo systemctl start vpp-snmp-agent
```
