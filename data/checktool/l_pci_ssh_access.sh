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
SSHPASS=1
SSHROOT=1
COMMAND='sshd -T'

#For debug
#set -x
#set -v

###################
##  Main process ##
###################
. /etc/profile

VERSION_OS=$(rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1)

# check if OS RedHat 5 and if sshd -T is working
if [[ $VERSION_OS -eq 5 ]]
        then
        $COMMAND > /dev/null 2>&1
        if [[ $? -eq 1 ]] ;then
                COMMAND='cat /etc/ssh/sshd_config'
        else
                COMMAND=`which sshd`' -T'
        fi
fi

# check in memory SSH config: password authentication forbidden

if [[ $($COMMAND | grep -m1 -ie '^passwordauthentication' | awk '{ print $2 }') == no ]]
        then
        SSHPASS=0
        else
        SSHPASS=1
fi

# check in memory SSH config: permit root login disabled

if [[ $($COMMAND | grep -m1 -ie '^permitrootlogin' | awk '{ print $2 }') == no ]]
        then
        SSHROOT=0
        else
        SSHROOT=1
fi

# Final result

if [[ $SSHPASS -eq 0 && $SSHROOT -eq 0 ]]
        then
                STATE=$STATE_OK
                echo "OK - Password Authentication and PermitRootLogin are disabled"
        else
                if [[ $SSHPASS -eq 1 && $SSHROOT -eq 0 ]]
                then
                        STATE=$STATE_WARNING
                        echo "Password Authentication is not correctly set"
                elif [[ $SSHPASS -eq 0 && $SSHROOT -eq 1 ]]
                then
                        STATE=$STATE_WARNING
                        echo "PermitRootLogin is not correctly set"

                else
                        STATE=$STATE_CRITICAL
                        echo "Problem - Password Authentication and PermitRootLogin are enabled"
                fi
fi

exit $STATE
