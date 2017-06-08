#!/bin/bash
#
# CODES retour checktoolV2 = ( OK => 0, WARNING => 1, CRITICAL => 2, UNKNOWN => 3 )
#
# PCI plugins for test value of Session logging TimeOut in variables $TMOUT

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
TIMEOUT=0
PCI_PROFILE=/etc/profile.d/pci.sh

#For debug
#set -x
#set -v

###################
##  Main process ##
###################
. /etc/profile

# test que la variable TMOUT est definie
if [ -z ${TMOUT+x} ]
then
        echo Timeout not set
        STATE=$STATE_CRITICAL
elif [ $TMOUT -eq 900 ]; then
	# check if timeout is defined with /etc/profile.d/pci.sh and if this file is readable for anyone
	if [ -f $PCI_PROFILE ]; then
        	PERM_PCI_PROFILE=$(stat -c '%A' $PCI_PROFILE | grep -o r | wc -l)
        	if [ $PERM_PCI_PROFILE -ne '3' ]; then
		STATE=$STATE_CRITICAL
		echo "KO - $PCI_PROFILE has bad permissions : $(stat -c '%a' $PCI_PROFILE)"
		exit $STATE
		fi
	fi
        STATE=$STATE_OK
        echo "OK - Session TimeOut have good value : $TMOUT "
        # test plus pousse : la variable TMOUT doit etre en lecture seule
        #if [ -z "$(readonly|grep TMOUT)" ]
        #then
        #       echo tmout not readonly
        #        STATE=$STATE_WARNING
        #else
        #        STATE=$STATE_OK
        #        echo "OK - Session TimeOut have good value : $TIMEOUT "
        #fi
else
        STATE=$STATE_CRITICAL
        echo Timeout bad value $TMOUT
fi
exit $STATE
