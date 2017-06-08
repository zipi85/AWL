#!/bin/bash
#
# CODES retour checktoolV2 = ( OK => 0, WARNING => 1, CRITICAL => 2, UNKNOWN => 3 )
#
# PCI plugins for test value of dont_blame_nrpe parameters

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
TAGPCI="PCI\W+[0-9]\.[0-9]\W+C(6|6\W+LIGHT|7)"
CHECKETC="^\-(a|w)\W+exit,always\W+-F\W+dir=\/etc\/\W+-F\W+perm=wa"
CHECKUSR="^\-a\W+exit,always\W+-F\W+arch=b64\W+-S\W+execve\W+-S\W+chown"
AUDITDR1="/etc/audit/audit.rules"
AUDITDR2="/etc/audit/rules.d/audit.rules"
AUDITCTLRULES=$(/sbin/auditctl -l)
VERSION_OS=$(rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1)

#Check OS
if [[ $VERSION_OS == "5" ]]; then OS="RH"
elif cat /etc/redhat-release | grep -sqi centos; then OS="C"
else OS="RH";fi

#For debug
#set -x
#set -v

###################
##  Main process ##
###################

#Check if AuditD rules file exists
if [ ! -f $AUDITDR1  -a ! -f $AUDITDR2 ]; then
        echo "KO - AuditD rules file not found"
        exit $STATE_CRITICAL
fi

#Check which kind of PCI template is present
if grep -sqiE $TAGPCI $AUDITDR1 $AUDITDR2; then
                TAG=$(grep -Eoh 'PCI\W+[0-9]\.[0-9]' $AUDITDR1 $AUDITDR2)
elif grep -sqi PCI $AUDITDR1 $AUDITDR2; then
                TAG="PCI"
else
                TAG="undefined"
fi

#Check if rules are loaded and which template is used
if [[ $AUDITCTLRULES == "No rules" ]]; then
                echo "KO - AuditD PCI rules are not loaded"
                STATE=$STATE_CRITICAL
else
                echo "OK - AuditD rules loaded from $OS$VERSION_OS $TAG template"
                STATE=$STATE_OK
fi
exit $STATE
