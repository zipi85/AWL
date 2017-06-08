#!/bin/bash
#
# CODES retour checktoolV2 = ( OK => 0, WARNING => 1, CRITICAL => 2, UNKNOWN => 3 );

##Definition
VERSION="1.0"
SCRIPTNAME=$0


# Plugin return codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3

#For debug
#set -v
#set -x

# Default variables
STATE=$STATE_UNKNOWN

if [[ -e '/bin/systemctl' ]]
        then
                if systemctl --type=service | grep snmpd | grep -qE "loaded\s+active\s+running" > /dev/null
                then
                SNMPSERV=1
                else
                SNMPSERV=0
                fi
        else    if service snmpd status 2>&1 | grep -sqi running
                then
                SNMPSERV=1
                else
                SNMPSERV=0
                fi
fi

if [[ $SNMPSERV -eq 0 ]]
        then
                STATE=$STATE_OK
                echo "OK - SNMP service is not running"
        else
                STATE=$STATE_CRITICAL
                echo "KO - SNMP service is running"
fi
exit $STATE

