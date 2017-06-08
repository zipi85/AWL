#!/bin/bash
#Code retour pour le check NRPE de Nagios
#
#0 OK The plugin was able to check the service and it appeared to be functioning properly
#1 Warning The plugin was able to check the service, but it appeared to be above some "warning" threshold or did not appear to be working properly
#2 Critical The plugin detected that either the service was not running or it was above some "critical" threshold
#3 Unknown Invalid command line arguments were supplied to the plugin or low-level failures internal to the plugin (such as unable to fork, or open a tcp socket) that prevent it from performing the specified operation. Higher-level errors (such as name resolution errors, socket timeouts, etc) are outside of the control of plugins and should generally NOT be reported as UNKNOWN states.
#
##Definition
VERSION="1.0"
SCRIPTNAME=l_pci_rsyslog

# Plugin return codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3

# Default variables
DESCRIPTION="Unknown"
STATE=$STATE_UNKNOWN

#For debug
#set -v
#set -x

if [ -f /etc/rsyslog.d/50_remote.conf ];then
        FILENAME=/etc/rsyslog.d/50_remote.conf
elif [ -f /etc/rsyslog.conf ];then
        FILENAME=/etc/rsyslog.conf
else
        echo "KO - No rsyslog configuration file found !"
        STATE=$STATE_CRITICAL
        exit $STATE
fi

PATERN1=$(grep -o -P -m1 "(syslog-pci-mutv|new-syslog-pci-mutv)" $FILENAME)
PATERN2=$(grep -o -P -m1 "(syslog-pci-muts|new-syslog-pci-muts)" $FILENAME)

# Default options
SYSLOG1=1
SYSLOG2=1

###################
##  Main process ##
###################

# Test vdm syslog
if [ ! -z $PATERN1 ]
        then
        SYSLOG1=0
        else
        SYSLOG1=1
fi

# Test scl syslog
if [ ! -z $PATERN2 ]
        then
        SYSLOG2=0
        else
        SYSLOG2=1
fi

#final result
if [[ $SYSLOG1 -eq 0 && $SYSLOG2 -eq 0 ]]
  then
        echo "OK - Rsyslog configuration : $PATERN1 and $PATERN2"
        STATE=$STATE_OK
  else
        if [[ $SYSLOG1 -eq 1 && $SYSLOG2 -eq 0 ]]
                then
                echo "Vendome syslog not present - Please fix it !"
                STATE=$STATE_WARNING
        elif [[ $SYSLOG1 -eq 0 && $SYSLOG2 -eq 1 ]]
                then
                echo "Seclin syslog not present - Please fix it !"
                STATE=$STATE_WARNING
        else
                echo "KO - The file $FILENAME has NOT syslog PCI configured"
                STATE=$STATE_CRITICAL
        fi
fi

# STATE return the value of the return code $?
exit $STATE
