#!/bin/ksh
###########################################################################
#
# Tripwire For Servers
#
# tripwire_check.ksh : Controle d'integrite systeme automatique
#
# Auteur : helene le 25/02/2008
# v2.0 (18/11/2016) - GMT ajout de la reinitialisation de la BDD tripwire
###########################################################################
# Chargement des variables d'environnement Tripwire
#. $HOME/.tripwire/environ

# Declaration des Variables
REP_REPORTS=/usr/local/tripwire/tfs/report
e_date=`date +"%y%m%d"`
e_heure=`date +"%H%M%S"`
NOMTRACE=$REP_REPORTS/tripwire_check.$e_date.$e_heure.log
NOMTRACE_TRIP=$REP_REPORTS/tripwire_check.$e_date.$e_heure.trip
NOMTRACE_WATCH=$REP_REPORTS/tripwire_check.$e_date
MACHINE=`hostname`

echo "Lancement controle d integrite Tripwire SYSTEM" >$NOMTRACE
echo "-----------------------------------------------" >>$NOMTRACE
echo "Lancement controle d integrite Tripwire SYSTEM"
echo "-----------------------------------------------"
echo "MACHINE : $MACHINE"
echo "MACHINE : $MACHINE" >>$NOMTRACE
echo "JOUR : $e_date              HEURE : $e_heure" >>$NOMTRACE
# Lancement du controle et recuperation du nom du rapport
/usr/local/tripwire/tfs/bin/tripwire --check 1>>$NOMTRACE_TRIP 2>&1
CODE_RETOUR=$?
/usr/bin/logger -f $NOMTRACE_TRIP -t 'tripwire' -p local2.info
if [ $CODE_RETOUR -ne 0 ] ;
then
echo "ERREUR dans le controle d integrite $0"
echo "Fichier rapport genere : "
grep "Wrote report file:" $NOMTRACE_TRIP | awk '{FS=":" ; print $4}'
#echo "Code retour : $CODE_RETOUR"
grep  "Total violations found:  0"  $NOMTRACE_TRIP
grep  "Total violations found:  0"  $NOMTRACE_TRIP >>$NOMTRACE
if [ $? -ne 0 ] ;
then
echo "------------------------------------------"
echo " ATTENTION : TRIPWIRE VIOLATIONS DETECTEES"
echo "------------------------------------------"
echo "------------------------------------------" >>$NOMTRACE
echo " ATTENTION : TRIPWIRE VIOLATIONS DETECTEES" >>$NOMTRACE
echo "------------------------------------------" >>$NOMTRACE
grep "Total violations found:" $NOMTRACE_TRIP
grep "Total violations found:" $NOMTRACE_TRIP >>$NOMTRACE
grep -i "Added object name" $NOMTRACE_TRIP
grep -i "Added object name" $NOMTRACE_TRIP >>$NOMTRACE
grep -i "Modified object name" $NOMTRACE_TRIP
grep -i "Modified object name" $NOMTRACE_TRIP >>$NOMTRACE
grep -i "Removed object name" $NOMTRACE_TRIP
grep -i "Removed object name" $NOMTRACE_TRIP >>$NOMTRACE
echo "-----------------------------------------"
echo "Reinitialisation BDD "
echo "-----------------------------------------"
VARPASSE_PART1=`echo $HOSTNAME | awk '{print substr($0,length($0)-1,1)}'`
VARPASSE_PART2=`echo $HOSTNAME | awk '{print substr($0,length($0)-2,1)}'`
VARPASSE=$VARPASSE_PART1$VARPASSE_PART2"tripwire"
/usr/local/tripwire/tfs/bin/tripwire --init -P $VARPASSE >>$NOMTRACE

echo "************************************" >>$NOMTRACE_WATCH
cat $NOMTRACE >>$NOMTRACE_WATCH
exit 1
fi
else
echo "---------------------------------"
echo " OK --> PAS DE VIOLATION DETECTEE"
echo "---------------------------------"
echo "---------------------------------" >>$NOMTRACE
echo " OK --> PAS DE VIOLATION DETECTEE" >>$NOMTRACE
echo "---------------------------------" >>$NOMTRACE
fi



# menage des fichiers rapports et des fichiers de logs
echo "----------------------------------" >>$NOMTRACE
echo "Suppression des fchiers suivants :" >>$NOMTRACE
echo "----------------------------------" >>$NOMTRACE
echo "-----------------------------------------"
echo "Suppression des vieux fichiers suivants :"
echo "-----------------------------------------"
find $REP_REPORTS -name "tripwire_check*" -mtime +30 -exec ls -al {} \; >>$NOMTRACE
find $REP_REPORTS -name "tripwire_check*" -mtime +30 -exec ls -al {} \;
find $REP_REPORTS -name "tripwire_check*" -mtime +30 -exec rm -rf {} \;
find $REP_REPORTS -name "$MACHINE-*" -mtime +30 -exec ls -al {} \; >>$NOMTRACE
find $REP_REPORTS -name "$MACHINE-*" -mtime +30 -exec ls -al {} \;
find $REP_REPORTS -name "$MACHINE-*" -mtime +30 -exec rm -rf {} \;

