#!/bin/bash
#
# CODES retour checktoolV2 = ( OK => 0, WARNING => 1, CRITICAL => 2, UNKNOWN => 3 )
#
# PCI plugins for test su binarie (on Isaac or Nim access)

##Definition
VERSION="1.0"
SCRIPTNAME=$0

#For debug
#set -x
#set -v

# Plugin return codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3


# Default variables
STATE=$STATE_UNKNOWN


###################
##  Main process ##
###################

# SU should be restricted either by pam/su or by linux permission (root:system 4750)
pam_auth=$(grep -e '^auth' /etc/pam.d/su|grep -v 'pam_rootok.so')
if [ -z "$pam_auth" ]
then
        echo "OK su usage restricted by pam/su"
        STATE=$STATE_OK
elif [ $(stat -c %u /bin/su) -eq 0 ] && [ "$(stat -c %G /bin/su)" == "system" ] && [ $(stat -c %a /bin/su) = "4750" ]
then
        echo "OK su usage restricted by linux perm"
        STATE=$STATE_OK
else
        echo "Ko su usage not restricted"
        STATE=$STATE_CRITICAL

fi

exit $STATE

