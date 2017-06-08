#!/bin/bash
#
# Nagios plugin in order to test last update date. If less than 3 month then OK, 3 months warning, more than 4 months Critical
# Syntax :  l_yum_lastupdate -w [Warning time (days)] -c [Critical time (days)]
# Exemple : l_yum_lastupdate -w 90 -c 120
# Beware ! Warning must be an integer below Critical. -w 6 -c 3 will not work !
#
# Written by Nicolas THEPOT 2012/01/14
# Modif le 14/02/2012 Par NTT ATTENTION ne fonctionne que sur des versions => a RedHat 5
# Added POD documentation HVE 17/09/2013
#Modif Mai 2016 par Erwn Breant
#Modif Juin 2016 par Ph Maupertuis prise en compte rh5
#Modif Octobre 2016 par T. Crosnier - Prise en compte MAJ SpaceWalk
#Modif Fevrier 2017 par T. Crosnier - Nouveau controle des updates
#set -xv

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
DESCRIPTION="Unknown"

# Default options
DELTA=0
WARNING_DAYS=30
CRITICAL_DAYS=90


test_date_yum () {
if [[ $DELTA -lt $CRITICAL_DAYS ]]
        then
                if [[ $DELTA -lt $WARNING_DAYS ]]
                then
                        STATE=$STATE_OK
                        echo "OK - $DELTA days since last Yum update"
                else
                        STATE=$STATE_WARNING
                        echo "WARNING - $DELTA days since last Yum update"
                fi
        else
                STATE=$STATE_CRITICAL
                echo "CRITICAL - $DELTA days since last Yum update !"
fi
}


# MAIN #

# check canal spacewalk
while read canal;do
        if [[ ! -z "${param// }" ]] ; then
                dt=$(echo $canal|awk -F'-' '{print $NF}')
                if [[ $(date -d$dt +"%Y%m") -ne $(date  +"%Y%m") ]]; then
                        echo $canal has a wrong date $dt
                        STATE=$STATE_CRITICAL
                        exit $STATE
                fi
        fi
done <<EOT
$(rhn-channel -l|grep cloned)
EOT



# Check return of "yum check-update"
yum check-update -d0 -q >/dev/null
result=$?
if [[ $result = 0 ]]
then
        # aucun update en attente -> sortie OK
        STATE=$STATE_OK
        echo OK - Server is up to date
        exit $STATE
fi

if [[ $result = 1 ]]
then
        # yum update indique des erreurs
        echo "KO - Errors found with 'yum check-update'"
        STATE=$STATE_CRITICAL
        exit $STATE
fi

#Vérification si les updates sont poussées par Spacewalk
if grep -sqi rhn_check /var/log/cron; then
                if grep -E 'Adding packages.*(kernel|tzdata)' /var/log/up2dat*  >/dev/null; then
                        DELTA=$(( (`date +%s` - `grep -hE 'Adding packages.*(kernel|tzdata)' /var/log/up2date* | head -n 1|cut -d ']' -f1 | sed -e 's/\[//g'|xargs -Idd date -d dd +%s`) /24 /3600))
                        test_date_yum
                        exit $STATE
                fi
fi

# Check version d'OS, sortie avec etat unknown si redhat5 (pas de yum history, pas de test)

VERSION_OS=$(rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1)

if [[ $VERSION_OS -eq 5 ]]; then
    dtboot=$(date -d $(who -b|awk '{print $3}') +'%a %d %b %Y')
    dt_eve_boot=$(date -d "$(who -b|awk '{print $3}') 1 day ago" +'%a %d %b %Y')
    nbrpm=$(( (`rpm -qa --last| grep "$dtboot"|wc -l` + `rpm -qa --last| grep "$dt_eve_boot"|wc -l`) ))
    if [[ $nbrpm -eq 0 ]] ;
    then
        STATE=$STATE_UNKNOWN
        echo No patch applied at the last reboot
    else
        DELTA=$(( (`date +%s` - `date -d $(who -b|awk '{print $3}') +'%s'`) /24 /3600))
        test_date_yum
    fi
else
#Check de l'historique de yum (voir si update de moins d'un mois)

    YUMHISTORY=$(yum history list all | grep U)
    IFS=$'\n'
    for line in $YUMHISTORY; do
      ID=$(echo $line | grep -oE '^\W+[0-9]{1,}' | grep -oE '[0-9]{1,}')
      if [[ ! -z $ID ]]; then
        STATUS=`yum history info $ID 2>&1 | grep -i -B1 "Command Line.*update" | sed "s/.* : //g" | sed "N;s/\n/;/g" | sed "s/-[^\S]\+//g" | sed "s/ //g"`

        if [[ "x${STATUS}x" == "xSuccess;updatex" ]]; then
          DELTA=$(( (`date +%s` - `echo $line |cut -d '|' -f 3|xargs -Idd date -d dd +%s`) /24 /3600))
          test_date_yum
          exit $STATE
        fi
      fi
    done
    echo KO - yum history has failed to find 'yum update' command
    STATE=$STATE_CRITICAL
fi
if [[ $STATE -eq $STATE_OK ]] ;then
        echo OK - Server is up to date
fi
exit $STATE
