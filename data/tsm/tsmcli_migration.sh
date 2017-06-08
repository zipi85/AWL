#!/bin/sh
#set -x
#----------------------------------------------------------------------------#
#                                                                            #
# definition of the script                                                   #
#============================================================================#
# tsm_migration.sh in /opt/backup/tsmcli
  SCRIPT_FULL=`basename $0`                  # script name with extension    #
  SCRIPT=`echo $SCRIPT_FULL| sed s/".sh"//g` # script name without extension #
  VERSION=v01.02 # portability for old bash (lower&uppercase) and test INSTANCE_NAME 08/02/2017 K. Favry     - WL-TO-CISS-CIS-XS-BSM
#  VERSION=v01.01 # comma bugfix, always yes, rollback 03/02/2017 K. Favry     - WL-TO-CISS-CIS-XS-BSM
#  VERSION=v01.00 # first realese  02/02/2017 K. Favry     - WL-TO-CISS-CIS-XS-BSM
# VERSION=v00.01 # created  31/01/2017 C. Delberghe - WL-TO-CISS-CIS-XS-BSM
#                                                                            #
#----------------------------------------------------------------------------#
#                                                                            #
# Topic              : Migration assistance from Mutualised TSM to PCI TSM
#                                                                            #
# Syntax             : $PATH_SRC/$SCRIPT_FULL <TSM_INSTANCE_NEW>
#                                                                            #
# Operating System   : Linux + TSM                                           #
#                                                                            #
# Input Files        : N/A                                                   #
#                                                                            #
# Output Files       : $PATH_OUT/$SCRIPT.*
#
# Log File           : $PATH_LOG/$SCRIPT.log  or/and
#                                                                            #
# User/Group/Permit  : root/backup/754                                       #
#                      are executed locally on the client TSM to migrate     #
#                                                                            #
#----------------------------------------------------------------------------#
#                                                                            #
# Return Code        : RC=0 normal end                                       #
#                      RC=1 end in error                                     #
#                      RC=2 end with warning                                 #
#                                                                            #
#----------------------------------------------------------------------------#
#                                                                            #
# definition of the variables                                                #
#============================================================================#
  HOST=`uname -n`
  FIC_LOG="`echo $SCRIPT`.`echo $HOST`.log"
  NB_ARG=$#
  DATE_DAY=`date "+%d/%m/%Y"`
  DATE=$DATE_DAY" a "`date "+%T"`
  DATE_LOG=`date "+%Y%m%d"`

  PATH_DSMC="/opt/tivoli/tsm/client/ba/bin"
  PATH_SRC=`dirname $0`
  FIC_SYS=`readlink -e $PATH_DSMC/dsm.sys`
  PATH_CONFIG=`dirname $FIC_SYS`
  PATH_OUT=/var/log/backup
  PATH_LOG=/var/log/backup
  if [ ! -d "$PATH_LOG" ]
  then
    mkdir -p $PATH_LOG
  fi

  RC_SCRIPT=0
  DEBUG=0
  YES=0

#----------------------------------------------------------------------------#
#                                                                            #
# declaration of the functions                                               #
#============================================================================#
#
#----------------------------------------------------------------------------#
# function : writing messages regarding the log lvl
#----------------------------------------------------------------------------#
log_message()
{
  date +"[%d/%m/%Y-%H:%M:%S] $*" |  tee -a $PATH_LOG/${FIC_LOG}
  return 0
}
#----------------------------------------------------------------------------#
# function : writing error messages to stderr and logfile + ended script     #
#----------------------------------------------------------------------------#
log_error()
{
  date +"[%d/%m/%Y-%H:%M:%S] $*" |  tee -a $PATH_LOG/${FIC_LOG}
  RC_SCRIPT=1
  function_ended
  return 1
}
#----------------------------------------------------------------------------#
# function : writing debug  messages to stderr and logfile                   #
#----------------------------------------------------------------------------#
log_debug()
{
  if [ "$DEBUG" = "1" ]
    then
       date +"[%d/%m/%Y-%H:%M:%S] $*" |  tee -a $PATH_LOG/${FIC_LOG}
  fi
  return 0
}
#----------------------------------------------------------------------------#
# function : End of script, exit with message and return code retour setting #
#----------------------------------------------------------------------------#
function_ended()
{
echo -n "For rollback: "
yellow "$rollback"
 case $RC_SCRIPT in
  0) # normal end
     log_message "[_END_____] $HOST : `green Normal` End of  $SCRIPT_FULL $VERSION "
     ;;

  1) # end in error
     log_message "[_END_____] $HOST : End in `red ERROR` of $SCRIPT_FULL $VERSION "
     ;;

  *) #  end with warning
     log_message "[_END_____] $HOST : End with `yellow WARNING` of $SCRIPT_FULL $VERSION "
     ;;
 esac
 exit $RC_SCRIPT
}

#----------------------------------------------------------------------------#
# function : print in color management                                       #
#----------------------------------------------------------------------------#
red () {
echo -e \\033[31m$* \\033[0m
}
green () {
echo -e \\033[32m$* \\033[0m
}
yellow () {
echo -e \\033[33m$* \\033[0m
}

#----------------------------------------------------------------------------#
# function : run $* and splash a colored status                              #
#----------------------------------------------------------------------------#
run () {
CMD=$*
eval $CMD
RC_CMD=$?
echo -n "$CMD:  " | tee -a $PATH_LOG/$FIC_LOG

if [ $RC_CMD -ne 0 ]
then
        red [KO] | tee -a $PATH_LOG/$FIC_LOG
        RC_SCRIPT=1
        function_ended
else
        green [OK] | tee -a $PATH_LOG/$FIC_LOG
fi
}

yesno () {
## until yes or no ask if exec $*
if [ $YES = 1 ];
then
        yellow "You will: $*"
        $*
else
        yellow "Do you wanna: $* ? (yes|y|no|n)"
        read reply
        case $reply in
            yes|y) $* ;;
            no|n) log_error   "[_ERROR___] migration breaked !";;
            *) yesno $* ;;
        esac
fi
}

#----------------------------------------------------------------------------#
# function : pcipwd fullfield NODE_PASSORD var with $1 then _ until NODE_PASSORD length=10
#----------------------------------------------------------------------------#
pcipwd () {
NODE_PASSWORD=$1
while [ ${#NODE_PASSWORD} -lt 10 ]
do
   NODE_PASSWORD="${NODE_PASSWORD}_"
done
}

go () {
echo
}

usage () {
      log_message "[_ERROR___] $HOST : $SCRIPT_FULL SYNTAX NOT OK "
      msg_error="CORRECT SYNTAX IS : ${PATH_SRC}/${SCRIPT_FULL} [-h|--help] <-i|--instance NEW_INSTANCE_NAME> [-y|--yes]"
      log_error   "[_ERROR___] $HOST : $msg_error"
}
#----------------------------------------------------------------------------#
#                                                                            #
# Main Program                                                               #
#============================================================================#
log_debug "[_DEBUG___] Main Program"
log_message "[_START___] $HOST : Starting $SCRIPT_FULL $VERSION "


log_debug   "[_DEBUG___] param = $*"
if ! options=$(getopt -o hi:y --long help,instance:,yes -- "$@")
then
     usage
fi

eval set -- "$options"

while [ $# -gt 0 ]
do
    case $1 in
    -h|--help) usage;;
    -i|--instance) INSTANCE_MAJ=`echo $2| tr '[:lower:]' '[:upper:]'`;INSTANCE_MIN=`echo $2| tr '[:upper:]' '[:lower:]'` ; shift;;
    -y|--yes) YES=1 ;;
    (--) shift; break;;
    (-*) echo "$0: error - unrecognized option $1" 1>&2; exit 1;;
    (*) break;;
    esac
    shift
done

for var in INSTANCE_MAJ INSTANCE_MIN
do
        if [ -z ${!var} ]
        then
                red "The $var variable is not set !"
                usage
        else
                log_debug   "[_DEBUG___] ${var} = ${!var}"
        fi
done





case ${INSTANCE_MAJ} in
  TSMQ11) # for testing
            TSMSRV_NEW=sqsmuq11s.data.priv.atos.fr
            IPSRV_NEW=10.28.118.142
            ;;
  TSM610) # for testing
            TSMSRV_NEW=spsmu610s.data.priv.atos.fr
            IPSRV_NEW=10.28.118.146
            ;;
  TSMPCI21) # for CTIS
            TSMSRV_NEW=spspci21s.data.priv.atos.fr
            IPSRV_NEW=10.26.172.81
            ;;
  TSMPCI31) # for CTIV
            TSMSRV_NEW=spspci31v.data.priv.atos.fr
            IPSRV_NEW=10.18.75.226
            ;;
  *)        # else
            log_error "[_ERROR___] Bad value for INSTANCE_MAJ `red ${INSTANCE_MAJ}`!"
            ;;

esac


if [ -r $FIC_SYS ]
  then
   echo "================================================="
   echo "Actual file : $FIC_SYS"
   echo "-------------------------------------------------"
   grep -v ^* $FIC_SYS | tee -a $PATH_LOG/$FIC_LOG
   echo "-------------------------------------------------"
   yesno go further
   echo "================================================="
  else
    log_error "[_ERROR___] $FIC_SYS not exit !"
fi

if [ `grep -v ^* $FIC_SYS | grep -ic SErvername` -gt 1 ]
  then
    log_error   "[_ERROR___] More than 1 SErvername into the $FIC_SYS file, too complex to industrialzed the migration!"
fi

INSTANCE_ACTUAL=`grep -v ^* $FIC_SYS | grep -i SErvername | awk  '{ print $2 }' | tr '[:lower:]' '[:upper:]' `
NODENAME=`cat $FIC_SYS | grep -v "^*" | grep -i nodename | awk  '{ print $2 }' | tr '[:lower:]' '[:upper:]' `

ls -1R $PATH_CONFIG/dsm*.opt > $PATH_LOG/$SCRIPT.dsmoptfiles

log_message "[_INFO____] List of dsm*.opt files :"
log_message "-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-"
cat $PATH_LOG/$SCRIPT.dsmoptfiles | tee -a $PATH_LOG/$FIC_LOG
log_message "-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-"

TSMSRV_ACTUAL=`grep -v ^* $FIC_SYS | grep -i tcpserveraddress | awk  '{ print $2 }' `

echo "================================================="
echo " Actual TSM server : $INSTANCE_ACTUAL on $TSMSRV_ACTUAL "
echo "-------------------------------------------------"
echo "    NEW TSM server : $INSTANCE_MAJ on $TSMSRV_NEW ( $IPSRV_NEW )"
echo "-------------------------------------------------"
yesno go further
echo "================================================="

echo "================================================="
echo " Your TSM user on $INSTANCE_ACTUAL ? "
echo "================================================="
read TSM_USER_ACTUAL
echo "================================================="
echo " Your password for $TSM_USER_ACTUAL on $INSTANCE_ACTUAL ? "
echo "================================================="
stty -echo
read TSM_USER_PWD_ACTUAL
stty echo

log_message "[_INFO____] $INSTANCE_ACTUAL : Formatting the command"
DSMADMC_ACTUAL="$PATH_DSMC/dsmadmc -se=$INSTANCE_ACTUAL -id=$TSM_USER_ACTUAL -pass=$TSM_USER_PWD_ACTUAL "
TSM_CDE_ACTUAL="$DSMADMC_ACTUAL -OUTfile"
TSM_CDE_TAB_ACTUAL="$DSMADMC_ACTUAL -NOConfirm -OUTfile -tabdelimited -dataonly=yes"
TSM_CDE_COMMA_ACTUAL="$DSMADMC_ACTUAL -NOConfirm -OUTfile -comma -dataonly=yes"

$TSM_CDE_TAB_ACTUAL "SELECT NODE_NAME,DOMAIN_NAME,CONTACT,PROXY_TARGET FROM NODES WHERE NODE_NAME='$NODENAME'" > $PATH_LOG/$SCRIPT.$NODENAME 2>>$PATH_LOG/${FIC_LOG}
log_message "[_INFO____] Information on node $NODENAME:"
log_message "-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-"
cat $PATH_LOG/$SCRIPT.$NODENAME | tee -a $PATH_LOG/$FIC_LOG
log_message "-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-"

NODE_DOMAIN=`cat $PATH_LOG/$SCRIPT.$NODENAME | awk -F"\t" '{ print $2 }' `
NODE_CONTACT=`cat $PATH_LOG/$SCRIPT.$NODENAME | awk -F"\t" '{ print $3 }' `
NODE_PROXY_TARGET=`cat $PATH_LOG/$SCRIPT.$NODENAME | awk -F"\t" '{ print $4 }'|tr ',' ' '`


if [ -n "$NODE_PROXY_TARGET" ]
   then
      for each in $NODE_PROXY_TARGET
      do
         $TSM_CDE_TAB_ACTUAL "SELECT NODE_NAME,DOMAIN_NAME,CONTACT,PROXY_TARGET FROM NODES WHERE NODE_NAME='$each'" > $PATH_LOG/$SCRIPT.$each 2>>$PATH_LOG/${FIC_LOG}
         log_message "[_INFO____] Information on node $NODENAME:"
         log_message "-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-"
         cat $PATH_LOG/$SCRIPT.$NODENAME | tee -a $PATH_LOG/$FIC_LOG
         log_message "-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-"
      done
fi


log_debug "[_DEBUG___] NODENAME=$NODENAME NODE_DOMAIN=$NODE_DOMAIN NODE_CONTACT=$NODE_CONTACT NODE_PROXY_TARGET=$NODE_PROXY_TARGET"

for dsmfiles in $FIC_SYS `cat $PATH_LOG/$SCRIPT.dsmoptfiles`
do
   date=`date +%Y%m%d.%H%M%S`
   cp -p $dsmfiles $dsmfiles.$date
   yesno run sed -i \"s/$INSTANCE_ACTUAL/$INSTANCE_MAJ/gi\" $dsmfiles
   yesno run sed -i \"s/$TSMSRV_ACTUAL/$TSMSRV_NEW/gi\" $dsmfiles
   echo;echo "================================================="
   echo "Difference between $dsmfiles and $dsmfiles.$date"
   diff $dsmfiles $dsmfiles.$date
   rollback="mv -f $dsmfiles.$date $dsmfiles;$rollback"
   echo "================================================="
done
echo "================================================="
echo " Your TSM user on $INSTANCE_MAJ ? "
echo "================================================="
read TSM_USER_NEW
echo "================================================="
echo " Your password for $TSM_USER_NEW on $INSTANCE_MAJ ? "
echo "================================================="
stty -echo
read TSM_USER_PWD_NEW
stty echo

DSMADMC_NEW="$PATH_DSMC/dsmadmc -se=$INSTANCE_MAJ -id=$TSM_USER_NEW -pass=$TSM_USER_PWD_NEW "
TSM_CDE_NEW="$DSMADMC_NEW -OUTfile"
TSM_CDE_TAB_NEW="$DSMADMC_NEW -NOConfirm -OUTfile -tabdelimited -dataonly=yes"
TSM_CDE_COMMA_NEW="$DSMADMC_NEW -NOConfirm -OUTfile -comma -dataonly=yes"
pcipwd `echo $NODENAME | tr '[:upper:]' '[:lower:]'`
yesno run $TSM_CDE_NEW  \"REGister Node $NODENAME ${NODE_PASSWORD} DOmain=$NODE_DOMAIN USerid=NONE CONtact=\'$NODE_CONTACT\'\"
rollback="$TSM_CDE_NEW  \"remove Node $NODENAME\";$rollback"
echo $rollback
yesno run $PATH_DSMC/dsmc SET Password ${NODE_PASSWORD} ${NODE_PASSWORD}
if [ -n "$NODE_PROXY_TARGET" ]
   then
      for each in $NODE_PROXY_TARGET
      do
         TARGET_DOMAIN=`cat $PATH_LOG/$SCRIPT.$each | awk -F"\t" '{ print $2 }' `
         TARGET_CONTACT=`cat $PATH_LOG/$SCRIPT.$each | awk -F"\t" '{ print $3 }' `
         log_debug "[_DEBUG___] TARGET_DOMAIN=$TARGET_DOMAIN TARGET_CONTACT=$TARGET_CONTACT"
         pcipwd `echo $each | tr '[:upper:]' '[:lower:]'`
         yesno run $TSM_CDE_NEW \"REGister Node $each ${NODE_PASSWORD} DOmain=$TARGET_DOMAIN USerid=NONE CONtact=\'$TARGET_CONTACT\'\"
         rollback="$TSM_CDE_NEW  \"remove Node $each\";$rollback"
         yesno run $TSM_CDE_NEW \"GRant PROXynode TArget=$each AGent=$NODENAME\"
       done
fi
#----------------------------------------------------------------------------#
#                                                                            #
# SCRIPT finished                                                            #
#============================================================================#
log_debug   "[_DEBUG___] Exit of script with return code $RC_SCRIPT"
function_ended "$RC_SCRIPT"
# Next line = security line => obligatory exit                               #
#----------------------------------------------------------------------------#
exit 1
