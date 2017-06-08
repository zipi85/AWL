#!/bin/bash
#
# CODES retour checktoolV2 = ( OK => 0, WARNING => 1, CRITICAL => 2, UNKNOWN => 3 )
#
# PCI plugins for test value of dont_blame_nrpe parameters

##Definition
VERSION="1.0"
SCRIPTNAME=$0


# Plugin return codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3


# Default variables
STATE=$STATE_UNKNOWN

#For debug
#set -x
#set -v

###################
##  Main process ##
###################

if grep -q dont_blame_nrpe=0 /etc/nagios/nrpe.cfg
        then
                STATE=$STATE_OK
                echo "OK - NRPE variable disabled"
        else
                STATE=$STATE_CRITICAL
                echo "Please Disable NRPE variable"
fi

exit $STATE
