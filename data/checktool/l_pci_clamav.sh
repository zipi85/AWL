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


# Default variables
STATE=$STATE_UNKNOWN

timestart=$(date +'%m/%d/%Y %T')
finalresult=$STATE_UNKNOWN
Gfreshcron=$STATE_UNKNOWN
freshdate=$STATE_UNKNOWN
clamcron=$STATE_UNKNOWN
clamrun=$STATE_UNKNOWN
clamsyslog=$STATE_UNKNOWN
freshwork=$STATE_UNKNOWN
clamwat=$STATE_UNKNOWN
clamvirus=$STATE_UNKNOWN

#For debug
#set -xv

if [ ! -f /etc/freshclam.conf ]
then
        echo KO - /etc/freshclam.conf not found !
        exit $STATE_CRITICAL
fi

osversion=$(rpm -qa \*-release | grep -Ei "oracle|redhat|centos" | cut -d"-" -f3|cut -c1)

## Test if freshclam running today (old)
#if grep -qi freshclam /var/log/cron; then echo -e \\t yes; else
#    ar=($(grep 'ClamAV update process started at' /var/log/clamav/freshclam.log|tail -n 1))
#    delta=$(date -d @$(( $(date +%s) -  $(date -d"${ar[7]} ${ar[6]} ${ar[9]}" +%s) )) +%s|xargs -I dd echo dd / 24 /3600 |bc)
#    if [[ $delta -lt 7 ]]; then echo -e \\t yes >>$FIC; else echo -e \\t no >>$FIC;okko=1;fi
#fi


## Test if freshclam running today
# Doesn't work if logrotate happended after freshclam ran
if [[ osversion -eq 5 ]];then
    freshcron=$STATE_OK
else 
    if grep -qi freshclam /var/log/cron
    then
	freshcron=$STATE_OK
    else
	freshcron=$STATE_CRITICAL
    fi
fi

freshlogfile=$(grep '^UpdateLogFile' /etc/freshclam.conf| awk {'print $2; '})
if [[ -f "$freshlogfile" ]]
then
    if [[  $(date +%s -d '1 day ago') -lt $(date +%s -r $freshlogfile) ]] 
    then
	freshdate=$STATE_OK
    else
	freshdate=$STATE_CRITICAL
    fi
fi

## Test if clamscan running
## We use gunzip in case cron log are compressed
if gunzip -cf $(ls -1t /var/log/cron*|head -n 2)|grep -sqi 'clamscan'
then
        clamcron=$STATE_OK
else
        clamcron=$STATE_CRITICAL
fi

## Test if last clamscan log is less than 7 days ago
clamlogfile=$(ls -1tr /var/log/clamav/clamscan.log* 2>/dev/null|tail -n 1)
if [[ -n $clamlogfile ]] ;  
then
    if [[ $(find "$clamlogfile" -mtime -7) ]]; then clamrun=$STATE_OK ; else clamrun=$STATE_CRITICAL; fi
fi
## Test if clamscan sending report to syslog
if grep -sqi logger /usr/local/etc/clamscan; then  clamsyslog=$STATE_OK; else clamsyslog=$STATE_CRITICAL;fi

## Test if freshclam working
# Not working with two freshclam without updates available
#grep -n 'ClamAV update process started' freshclam.log|tail -n 1|cut -d':'  -f1|xargs -I nn tail -n +nn freshclam.log
if [ -f "$freshlogfile" ]; then 
    freshresult=$(grep -n 'ClamAV update process started' $freshlogfile|tail -n 1|cut -d':'  -f1|xargs -I nn tail -n +nn $freshlogfile)
    if (grep -qE 'main.cvd is up to date.*daily.cvd is up to date.*bytecode.cvd is up to date|Database updated' <<<$freshresult) ;then  freshwork=$STATE_OK; else freshwork=$STATE_CRITICAL;fi
fi

## Test if watchdog is configured for monitor infected files
if grep -sq '!Infected files: 0' /{usr/local/watch,etc/watchdot}/logmon.cfg ; then  clamwat=$STATE_OK; else clamwat=$STATE_CRITICAL;fi

## Test if clamscan find some virus
if [ $clamrun = 0 ]
then
    if grep -qe 'Infected files: [^0]' $clamlogfile
    then
	    clamvirus=$STATE_WARNING
    elif grep -qe 'Infected files: [0]' $clamlogfile;then
	    clamvirus=$STATE_OK
    fi
fi


## Final result
finalresult=$(echo -e  "$freshcron \n $freshdate \n $clamcron \n $clamrun \n $clamsyslog \n $freshwork \n $clamwat"|sort -rn|head -n 1)
if [ $finalresult = $STATE_OK ]
then
    echo "OK - (Requirement 5 fulfilled)"
elif [ $finalresult = $STATE_WARNING ] ; then
    echo "Clamscan find infected files"
else
    if [[ osversion -eq 5 ]]; then 
	    echo freshdate:$freshdate clamcron:$clamcron clamrun:$clamrun clamsyslog:$clamsyslog freshwork:$freshwork clamwat:$clamwat clamvirus:$clamvirus
    else
	    echo freshcron:$freshcron freshdate:$freshdate clamcron:$clamcron clamrun:$clamrun clamsyslog:$clamsyslog freshwork:$freshwork clamwat:$clamwat clamvirus:$clamvirus
    fi
fi

exit $finalresult

