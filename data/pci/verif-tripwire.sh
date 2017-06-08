#!/bin/bash
# def du fichier de traces
timestart=$(date +'%m/%d/%Y %T')
HOSTNAME=$(hostname)
FIC=/home/$SUDO_USER/$HOSTNAME-verif-tripwire.txt
touch $FIC
chown $SUDO_USER $FIC

okko=0
echo "############################">>$FIC
date >$FIC
touch /tmp/a_week_ago -d'1 week ago 00:00'
echo -n Is tripwire scheduled : >>$FIC
if grep -sqi tripwire $(ls -1t /var/log/cron*|head -n 2); then  echo -e \\t yes >>$FIC; else echo -e \\t no >>$FIC ;okko=1;fi
echo -n Is tripwire sending report to syslog :>>$FIC
if grep -sqi logger /usr/local/tripwire/tfs/gentrip/tripwire_check.ksh; then  echo -e \\t yes >>$FIC; else echo -e \\t no >>$FIC ;okko=1;fi
echo -n Is tripwire running :>>$FIC
if [[ $(find /usr/local/tripwire/tfs/report/ -type f -newer /tmp/a_week_ago|xargs -Iff ls -l ff|wc -l) -gt 0 ]]; then  echo -e \\t yes >>$FIC ; else echo -e \\t no >>$FIC ;okko=1;fi
rm /tmp/a_week_ago
if  [[ $okko -eq 1 ]]; 
then
echo >>$FIC
echo tripwire ko:$(hostname) >>$FIC
else
echo tripwire ok:$(hostname) >>$FIC
fi
exit $okko
