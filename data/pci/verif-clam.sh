#!/bin/bash
# def du fichier de traces
timestart=$(date +'%m/%d/%Y %T')
HOSTNAME=$(hostname)
FIC=/home/$SUDO_USER/$HOSTNAME-verif-clam.txt
touch $FIC
rm $FIC
touch $FIC
chown $SUDO_USER $FIC
#
#
okko=0
echo "############################">>$FIC
date >$FIC
echo -n Is freshclam running : >>$FIC
if grep -qi freshclam /var/log/cron; then echo -e \\t yes; else
    ar=($(grep 'ClamAV update process started at' /var/log/clamav/freshclam.log|tail -n 1))
    delta=$(date -d @$(( $(date +%s) -  $(date -d"${ar[7]} ${ar[6]} ${ar[9]}" +%s) )) +%s|xargs -I dd echo dd / 24 /3600 |bc)
    if [[ $delta -lt 7 ]]; then echo -e \\t yes >>$FIC; else echo -e \\t no >>$FIC;okko=1;fi
fi
 echo -n Is clamscan running :>>$FIC
 if grep -sqi clamscan $(ls -1t /var/log/cron*|head -n 2); then  echo -e \\t yes>>$FIC; else echo -e \\t no >>$FIC ;okko=1;fi
echo -n Is clamscan sending report to syslog :>>$FIC
if grep -sqi logger /usr/local/etc/clamscan; then  echo -e \\t yes >>$FIC; else echo -e \\t no >>$FIC ;okko=1;fi
echo -n Is freshclam working :>>$FIC
if tail  -n2 /var/log/clamav/freshclam.log|grep -q 'Database updated'; then  echo -e \\t yes >>$FIC ; else echo -e \\t no >>$FIC ;okko=1;fi
echo -n Is  watchdog ok :>>$FIC
if grep -sq '!Infected files: 0' /{usr/local/watch,etc/watchdot}/logmon.cfg ; then  echo -e \\t yes >>$FIC; else echo -e \\t no >>$FIC ;okko=1;fi
if  [[ $okko -eq 1 ]]; 
then
echo>>$FIC
echo req5 ko:$(hostname)>>$FIC
else>>$FIC
echo req5 ok:$(hostname)>>$FIC
fi
exit $okko>>$FIC
echo "############################">>$FIC
