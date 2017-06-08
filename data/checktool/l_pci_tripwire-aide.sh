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
finalresult=$STATE_UNKNOWN
aidecron=$STATE_UNKNOWN
aiderun=$STATE_UNKNOWN
tripcron=$STATE_UNKNOWN
triplogger=$STATE_UNKNOWN
triprun=$STATE_UNKNOWN

###################
##  Main process ##
###################

## Check if AIDE or Tripwire are installed

VERSION_OS=$(rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1)

if rpm -qa | grep aide > /dev/null
then
        APP=AIDE
        if gunzip -cf $(ls -1t /var/log/cron*|head -n 2)|grep -sqi 'aide'; then aidecron=$STATE_OK; else aidecron=$STATE_CRITICAL;fi
        if find /var/log/aide/aide.log -mtime -7 > /dev/null; then aiderun=$STATE_OK; else aiderun=$STATE_CRITICAL;fi
elif [ -f /usr/local/tripwire/tfs/policy/policy.txt ]
then
        APP=Tripwire
        touch /tmp/a_week_ago -d'1 week ago 00:00'
        if gunzip -cf $(ls -1t /var/log/cron*|head -n 2)|grep -sqi 'tripwire'; then tripcron=$STATE_OK; elif crontab -u root -l|grep -sqiE '^[^#].+tripwire_check.ksh'; then tripcron=$STATE_OK; else tripcron=$STATE_CRITICAL;fi
        if grep -sqi logger /usr/local/tripwire/tfs/gentrip/tripwire_check.ksh; then triplogger=$STATE_OK; else triplogger=$STATE_CRITICAL;fi
        if [[ $(find /usr/local/tripwire/tfs/report/ -type f -newer /tmp/a_week_ago|xargs -Iff ls -l ff|wc -l) -gt 0 ]]; then triprun=$STATE_OK; else triprun=$STATE_CRITICAL;fi
        rm -f /tmp/a_week_ago
else
        if [ $VERSION_OS -gt 6 ]; then
                echo KO - AIDE is not installed
                exit $STATE_CRITICAL
        else
                echo KO - No integrity check tool installed
                exit $STATE_CRITICAL
        fi
fi

## Final result
if [ $APP = AIDE ]
then
        finalresult=$(echo -e  "$aidecron \n $aiderun"|sort -rn|head -n 1)
        if [ $finalresult = $STATE_OK ]; then
                echo "$APP OK - (Requirement 2 fulfilled)"
        else
                echo $APP KO - aidecron:$aidecron aiderun:$aiderun
        fi
else
        finalresult=$(echo -e  "$tripcron \n $triplogger \n $triprun"|sort -rn|head -n 1)
        if [ $finalresult = $STATE_OK ]; then
                echo "$APP OK - (Requirement 3 fulfilled)"
        else
                echo $APP KO - tripcron:$tripcron triplogger:$triplogger triprun:$triprun
        fi
fi
exit $finalresult
