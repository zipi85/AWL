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
AUDIT=1
CHKAUDIT=1
SYSLOGACTIVE=1

if /sbin/auditctl -s | grep -qe 'enabled[=| ]1'
        then
        AUDIT=0
fi

if [[ -e '/bin/systemctl' ]]
        then
                if systemctl --type=service | grep auditd | grep -q "loaded active running" > /dev/null
                then
                CHKAUDIT=0
                else
                CHKAUDIT=1
                fi
        else    if /sbin/chkconfig --list auditd | grep -q '3:on'
                then
                CHKAUDIT=0
                else
                CHKAUDIT=1
                fi
fi

if grep -sqiE '^active.*yes' /etc/audisp/plugins.d/syslog.conf
	then
	SYSLOGACTIVE=0
fi

if [[ $AUDIT -eq 0 && $CHKAUDIT -eq 0 && $SYSLOGACTIVE -eq 0 ]]
        then
        	STATE=$STATE_OK
        	echo "Ok - Good configuration for Auditd"
        elif  [[ $AUDIT -eq 1 && $CHKAUDIT -eq 1 ]]
                then
                STATE=$STATE_CRITICAL
                echo "Auditd don't work"
	elif [[ $SYSLOGACTIVE -eq 1 ]]
		then
                STATE=$STATE_CRITICAL
                echo "Syslog plugin is set to 'no'!"
	else
                STATE=$STATE_WARNING
                echo "Please verify if Auditd is enable"
fi

exit $STATE
