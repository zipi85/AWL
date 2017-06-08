#!/bin/bash
#
# CODES retour checktoolV2 = ( OK => 0, WARNING => 1, CRITICAL => 2, UNKNOWN => 3 )
#
# PCI plugins

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

if cat /etc/redhat-release | grep "release 7"> /dev/null; then
        STATE=$STATE_OK
        echo "OK - No need Hardening RPM on Centos 7"
	exit $STATE
fi	

if yum info installed awl-hardening-tools > /dev/null
        then
        rpmversion=$(yum info installed awl-hardening-tools | grep Version -m1 | awk '{print $3}')
        if [ "$rpmversion" != 1.1.0 ]; then
                STATE=$STATE_WARNING
                echo "WARNING - Old Hardening rpm : $rpmversion"
        else
                STATE=$STATE_OK
                echo "OK - Hardening rpm $rpmversion is installed"
        fi
else
        STATE=$STATE_CRITICAL
        echo "KO - Hardening rpm is not installed"
fi
exit $STATE
