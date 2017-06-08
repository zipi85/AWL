#!/bin/bash 
# def du fichier de traces
timestart=$(date +'%m/%d/%Y %T')
[[ -f "/usr/local/openssh/etc/sshd_config" ]] && SSHDFILE="/usr/local/openssh/etc/sshd_config" || SSHDFILE="/etc/ssh/sshd_config"
HOSTNAME=$(hostname)
#touch /home/$SUDO_USER/$HOSTNAME-traces-audit-2014.txt
#chown system:system /home/system/$HOSTNAME-traces-audit-2014.txt
FIC=/home/$SUDO_USER/$HOSTNAME-traces-audit-2016.txt
touch $FIC
chown $SUDO_USER $FIC

echo "###########################################################"
date >$FIC
echo "###########################################################" >>$FIC
#liste des commandes envoyée dans un fichier de traces
echo "UNAME">>$FIC
echo "">>$FIC
uname -a>>$FIC
echo "############################">>$FIC
echo "IFCONFIG">>$FIC
echo "">>$FIC
ifconfig -a >>$FIC
echo "############################">>$FIC
echo "NETSTAT">>$FIC
echo "">>$FIC
netstat -an | grep LISTEN>>$FIC
echo "############################">>$FIC
echo "NETSTAT UDP">>$FIC
echo "">>$FIC
netstat -an | grep -i UDP>>$FIC
echo "############################">>$FIC
echo "DF">>$FIC
echo "">>$FIC
df -k>>$FIC
echo "############################">>$FIC
echo "PS">>$FIC
echo "">>$FIC
ps -ef>>$FIC
echo "############################">>$FIC
echo "SSHD-CONFIG">>$FIC
echo "">>$FIC
grep PermitRootLogin $SSHDFILE |grep -vE '^\s*#'>>$FIC
echo "">>$FIC
echo "">>$FIC
grep Protocol $SSHDFILE>>$FIC
echo "">>$FIC
echo "">>$FIC
grep Authentication $SSHDFILE |grep -vE '^\s*#' >>$FIC
echo "">>$FIC
echo "">>$FIC
grep -vE '^\s*#|^$' $SSHDFILE >>$FIC
echo "############################">>$FIC
echo "NTP">>$FIC
echo "">>$FIC
grep server /etc/ntp.conf>>$FIC
echo "############################">>$FIC
echo "RSYSLOG">>$FIC
echo "">>$FIC
if [ -f /etc/rsyslog.conf ]
then grep "syslog-pci-mut"  /etc/rsyslog.conf /etc/rsyslog.d/*.conf >>$FIC
else grep "syslog-pci-mut"  /etc/syslog-ng/syslog-ng.conf>>$FIC
fi
echo "############################">>$FIC
echo "TRIPWIRE CRONTAB">>$FIC
echo "">>$FIC

if [ -f /etc/cron.d/tripwire ]
then cat /etc/cron.d/tripwire >>$FIC
else crontab -l | grep trip>>$FIC
fi

echo "TRIPWIRE FILE">>$FIC
cat /usr/local/tripwire/tfs/policy/policy.txt | grep  -v "#" | grep -v ^$ >>$FIC
echo "############################">>$FIC
echo "Passwd file " >>$FIC
cat /etc/passwd >>$FIC
echo "############################">>$FIC
echo "Updates pending " >>$FIC
yum check-update >>$FIC
echo pending_updates:$? >>$FIC

echo "############################">>$FIC
echo "Installed RPM " >>$FIC
rpm -qa --last >> $FIC
echo "############################">>$FIC
echo "Sudoers " >> $FIC
cat /etc/sudoers >> $FIC
if [ -d /etc/sudoers.d ]; then
	for x in $(ls -1 /etc/sudoers.d/*)
	do
		echo "" >> $FIC
		echo $(basename $x) >> $FIC
		cat $x >> $FIC
	done
fi
echo "############################">>$FIC
echo "Antivirus " >> $FIC
echo "Antivirus rpm " >> $FIC
rpm -q clamav >> $FIC >> $FIC
echo "Antivirus crontab" >> $FIC
cat /etc/cron.d/clamscan >> $FIC
echo "Antivirus update crontab" >> $FIC
cat /etc/cron.daily/freshclam >> $FIC
echo "Antivirus centralize report" >> $FIC
cat /usr/local/etc/clamscan >> $FIC
echo "############################">>$FIC
echo "Active auditctl " >> $FIC
auditctl -l >> $FIC
echo "############################">>$FIC
echo "Ausearch this script " >> $FIC
ausearch -ul $SUDO_USER -ts $timestart -i >> $FIC

echo "End of collect">>$FIC
