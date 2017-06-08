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

###################
##  Main process ##
###################

if rpm -qa | grep tws > /dev/null; then
        exclude+="|maestro"
fi

if rpm -qa | grep ricci > /dev/null; then
        exclude+="|ricci"
fi

if [[ $(sudo getent shadow | grep -vE '^[^:]*:(!{1,2}|0|\*):' |grep -vE 'root'$exclude|wc -l ) -gt 0 ]]
then
    user=`sudo getent shadow | grep -vE '^[^:]*:(!{1,2}|0|\*):' |grep -vE 'root'$exclude|cut -d':' -f1| tr '\n' ',' | sed -r 's/,$//g'`
    echo "KO - User(s) found with password ($user)"
        STATE=$STATE_CRITICAL
else
    echo OK - No user found with password
        STATE=$STATE_OK
fi
exit $STATE
