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
TEMPDIR=$(mktemp -d)
TEMPFILE=$TEMPDIR'/test_umask'
PCIPROFILE='/etc/profile.d/pci.sh'

#For debug
#set -x
#set -v

###################
##  Main process ##
###################

if [ -f $PCIPROFILE ]; then
        if grep -sqiE '^umask\s+[0]?027' $PCIPROFILE;then
                TESTREAD=$(stat -c '%A' $PCIPROFILE | grep -o r | wc -l)
                if [ $TESTREAD == '3' ]; then
                        echo "OK - Umask 027 defined in $PCIPROFILE";exit $STATE_OK
                else
                        echo "WARNING - Umask 027 defined but pci.sh not fully readable : $(stat -c '%a' $PCIPROFILE)";exit $STATE_WARNING;fi
        elif [[ -e '/bin/systemctl' ]];then
                echo "KO - Umask not defined in $PCIPROFILE";exit $STATE_CRITICAL;fi
fi

touch $TEMPFILE
OTHERS=`stat -c '%a' $TEMPFILE | cut -c 3`

# other permissions value ?
if [ $OTHERS == '0' ]
        then
                STATE=$STATE_OK
                echo "OK - Others have no permissions"
        else
                STATE=$STATE_CRITICAL
                echo "KO - Current Others permissions : $OTHERS"
fi
rm -Rf $TEMPDIR
exit $STATE
