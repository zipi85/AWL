#!/bin/bash
# def du fichier de traces
timestart=$(date +'%m/%d/%Y %T')
HOSTNAME=$(hostname)

timestart=$(date +'%m/%d/%Y %T') 
FIC=/home/$SUDO_USER/$HOSTNAME-traces-user-appli-audit
rm $FIC
touch $FIC
chown $SUDO_USER $FIC

echo timestart is $timestart>>$FIC
grep -o -w   '^\w\{3,3\}' /etc/passwd|grep -vE 'bin|ntp|adm|ftp|rpc|www|dba|rpc|rpm' |tail -n 1|while read uu
do
(su -l ${uu} <<EOF
getent passwd ${uu}
env|grep TMOUT
touch verif_audit_appli
rm verif_audit_appli
EOF
) >>$FIC
/sbin/ausearch --input-logs -ul ${SUDO_USER} -ui ${uu} -ts ${timestart} -i >>$FIC
done
