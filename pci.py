import os
import StringIO
import random
import datetime
import time
from fabric.api import *
from fabric.operations import put, require
from fabric.contrib.files import exists, contains, append, first, sed
from awl_bfi_fabric.conf.settings import DATA_DIR
from fabric import state

# source files
source = os.path.join(DATA_DIR, 'pci')
script = 'script-audit.56.sh'
clamscan = 'clamscan'
clamscansips = 'clamscan-sips'
clamwat = 'clamwat'
freshclam = 'freshclam'
freshdaily = 'freshdaily'
freshrotate = 'freshrotate'
clamavpuppet = 'clamav-puppet'
aidepuppet = 'aide-puppet'
auditdconfc6 = 'auditdrulesC6'
auditdconfc6light = 'auditdrulesC6light'
auditdconfc7 = 'auditdrulesC7'

@task()
def action_item():
    ''' collect evidences for action item '''
    YYYY=datetime.datetime.now().strftime ("%Y")
    for script in ('check_antivirus','action_item_72','action_item_71'):
	    lscript=os.path.join(source,script)
	    put(local_path=lscript, remote_path=script, mode=0755)
	    sudo(('/home/$SUDO_USER/%s')%(script))
	    nom_host=run('uname -n')
	    get(nom_host+'-'+script+'-'+YYYY+'.txt','~/audit/')

@task()
def check_ldap():
    ''' check if server is set with ldap '''
    x=sudo('''grep -E '^ldap_access_filter' /etc/sssd/sssd.conf''',quiet=True)
    print x+'\n'

@task()
def script_audit():
    ''' run specific script for PCI audit '''
    script = 'script-audit.56.sh'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    #run('chmod +x script-audit.56.sh') 
    sudo('/home/$SUDO_USER/script-audit.56.sh')
    nom_host=run('uname -n')
    get(nom_host+'-traces-audit-2016.txt','~/audit/')

@task()
def verif_audit_appli():
    ''' run specific script to check that applicatif users are audited '''
    script = 'verif-audit-appli.sh'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    sudo('/home/$SUDO_USER/verif-audit-appli.sh',warn_only=True)
    nom_host=run('uname -n')
    get(nom_host+'-verif-audit-appli.txt','~/audit/')

@task()
def verif_audit_filesystem_size():
    ''' run specific script to check the filesystem size '''
    state.output.everything = True
    sudo('df -h | grep var | grep log',warn_only=False)


@task()
def verif_tripwire():
    ''' run specific script to check that tripwire is running '''
    script = 'verif-tripwire.sh'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    sudo('/home/$SUDO_USER/verif-tripwire.sh',warn_only=True)
    nom_host=run('uname -n')
    get(nom_host+'-verif-tripwire.txt','~/audit/')

@task()
def verif_clam():
    ''' run specific script to check that clam is ok '''
    script = 'verif-clam.sh'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    sudo('/home/$SUDO_USER/verif-clam.sh',warn_only=True)
    nom_host=run('uname -n')
    get(nom_host+'-verif-clam.txt','~/audit/')

@task()
def check_java_package():
    ''' Check java package '''
    x=sudo('rpm -qa | grep awl-java',quiet=True)
    if x.succeeded:
	print '\033[96m'+x+'\033[0m'
    else:
	print '\033[91mNo extendedpackage installed...\033[0m'

@task()
def update_java():
    ''' Update Java '''
    if not exists('/etc/yum.repos.d/pvm.repo', use_sudo=True):
        sudo('yum install -y repositories-pvm --enablerepo=awl-main')
    scriptjava = 'feed_java.sh'
    lscript=os.path.join(source,scriptjava)
    put(local_path=lscript, remote_path=scriptjava, mode=0755)
    state.output.everything = True
    sudo('/home/$SUDO_USER/'+scriptjava)

@task()
def os_version():
    ''' Display OS version '''
    x=sudo('cat /etc/redhat-release',quiet=True)
    print '\033[96m'+x+'\033[0m'

@task()
def check_auditd_rules():
    ''' check if bdd user (sybase,mysql,oracle) are present in auditd rules file with "OPEN-OPENAT"'''
    x=sudo('''grep -E '^[^#].+-S open.+(sybase|mysql|oracle)' /etc/audit/rules.d/audit.rules /etc/audit/audit.rules''',warn_only=True,quiet=True)
    if x.succeeded:
    	print '\033[91m'+x+'\033[0m'

@task()
def check_antivirus():
    ''' Lance differentes verification de la configuration de clamav sur un serveur'''
    YYYY=datetime.datetime.now().strftime ("%Y")
    script = 'check_antivirus'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    sudo(('/home/$SUDO_USER/%s')%(script))
    nom_host=run('uname -n')
    get(nom_host+'-'+script+'-'+YYYY+'.txt','~/audit/')

@task()
def check_clamav_tripwire_logmon():
    '''Check duplicates CLAMAV and tripwire lines in logmon.cfg'''
    x=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    if ( x != "None"):
	clamavcheck=sudo('grep /var/log/clamav/clamscan.log ' +x+ ' | wc -l',warn_only=True,quiet=True)
	if clamavcheck == '0':
		print "\033[91mClamAV conf not found !\033[0m"
        elif clamavcheck != '1':
                print "\033[91mClamAV conf found " +clamavcheck+ " times !\033[0m"
	if sudo('''grep -E '^[^\#].+/usr/local/tripwire/tfs/report/tripwire_check' '''+x,warn_only=True,quiet=True).succeeded:
		print "\033[91mTripwire conf found !\033[0m"
        if sudo('''ps -ef | grep -iE 'watchdot.*start' | grep -v grep''',warn_only=True,quiet=True).failed:
                print "\033[91mWatchdog is not started !\033[0m"
    else:
        print '\033[91mNo watchdog config file found !\033[0m'

@task()
def install_aide():
    '''Install AIDE'''
    lscan=os.path.join(source,aidepuppet)
    put(local_path=lscan, remote_path='/etc/puppet/modules/aide-puppet.tar',use_sudo=True,mode=0755)
    sudo('tar -xf /etc/puppet/modules/aide-puppet.tar --directory=/etc/puppet/modules')
    sudo('''echo class { 'aide': } > /etc/puppet/modules/test.pp''')
    sudo('yum-config-manager --enable epel > /dev/null')
    x=sudo('puppet apply --test /etc/puppet/modules/test.pp',warn_only=True)
    if x.return_code > 2:
        print '\033[91mAIDE installation failed\033[0m'
        sudo('yum-config-manager --disable epel > /dev/null')
        return 1
    sudo('yum-config-manager --disable epel > /dev/null')
    sudo('rm -f /etc/puppet/modules/aide-puppet.tar')


@task()
def install_clamav():
    '''Install CLAMAV with new PCI CLAMAV mirror'''
    if run('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        lscan=os.path.join(source,clamavpuppet)
        put(local_path=lscan, remote_path='/etc/puppet/modules/clamav-puppet.tar',use_sudo=True,mode=0755)
        sudo('tar -xf /etc/puppet/modules/clamav-puppet.tar --directory=/etc/puppet/modules')
        sudo('''echo class { 'clamav': } > /etc/puppet/modules/test.pp''')
        sudo('yum-config-manager --enable epel > /dev/null')
        x=sudo('puppet apply --test /etc/puppet/modules/test.pp',warn_only=True)
        if x.return_code > 2:
                print '\033[91mInstallation de CLAMAV KO\033[0m'
                sudo('yum-config-manager --disable epel > /dev/null')
                return 1
        sudo('yum-config-manager --disable epel > /dev/null')
        sudo('rm -f /etc/puppet/modules/clamav-puppet.tar')
        user='clamupdate'
    else:
    	if not exists('/etc/yum.repos.d/pvm.repo', use_sudo=True):
    		sudo('yum install -y repositories-pvm --enablerepo=awl-main')
    		sudo('yum-config-manager --disable pvm-main --disable pvm-external > /dev/null')
    	x=sudo('rpm -q clamav',warn_only=True,quiet=True)
        if x.succeeded:
                sudo('yum update -y clamav --enablerepo=pvm-main --enablerepo=pvm-external')
        else:
                sudo('yum install -y clamav --enablerepo=pvm-main --enablerepo=pvm-external')
        user='clam'

    #Push configuration files with good rights and specific user depending os version
    lscan=os.path.join(source,freshclam)
    put(local_path=lscan, remote_path='/etc/freshclam.conf',use_sudo=True,mode=0700)
    sudo('''sed -i 's/DatabaseOwner/DatabaseOwner '''+user+'''/g' /etc/freshclam.conf''')
    sudo('chown root: /etc/freshclam.conf')
    lscan=os.path.join(source,freshdaily)
    put(local_path=lscan, remote_path='/etc/cron.daily/freshclam',use_sudo=True,mode=0700)
    sudo('''sed -i 's/clam.clam/'''+user+''':'''+user+'''/g' /etc/cron.daily/freshclam''')
    sudo('chown root: /etc/cron.daily/freshclam')
    lscan=os.path.join(source,freshrotate)
    put(local_path=lscan, remote_path='/etc/logrotate.d/freshclam',use_sudo=True,mode=0644)
    sudo('''sed -i 's/clam clam/'''+user+''' '''+user+'''/g' /etc/logrotate.d/freshclam''')
    sudo('chown root: /etc/logrotate.d/freshclam')
    clamcron=StringIO.StringIO( ('%02d %02d * * sun   root    /usr/local/etc/clamscan &> /dev/null\n')%(random.randint(0,59),random.randint(6,12)))
    put(clamcron,'/etc/cron.d/clamscan',use_sudo=True,mode=0600)
    sudo('chown root: /etc/cron.d/clamscan')
    if run("hostname | grep sips",quiet=True):
        lscan=os.path.join(source,clamscansips)
    else:
        lscan=os.path.join(source,clamscan)
    put(local_path=lscan, remote_path='/usr/local/etc/clamscan',use_sudo=True,mode=0700)
    sudo('chown root: /usr/local/etc/clamscan')
    if not exists('/var/lib/clamav', use_sudo=True):
        sudo('mkdir -p /var/lib/clamav')
    sudo('chown -R '+user+':'+user+' /var/lib/clamav')
    if exists('/var/log/freshclam.log', use_sudo=True):
        sudo('chown '+user+':'+user+' /var/log/freshclam.log')
    if not exists('/var/log/clamav', use_sudo=True):
        sudo('mkdir -p /var/log/clamav')
    sudo('chown -R '+user+':'+user+' /var/log/clamav')
    if exists('/var/lib/clamav/mirrors.dat', use_sudo=True):
        sudo('rm /var/lib/clamav/mirrors.dat')
    if exists('/usr/share/doc/clamav-0.*/signatures.pdf', use_sudo=True):
        sudo('rm /usr/share/doc/clamav-0.*/signatures.pdf')
    x=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    if ( x != "None"):
        print "logmon.cfg present"
        if sudo("grep -P '/var/log/clamav/clamscan.log' "+x,quiet=True):
            print "entree clamav trouvee dans logmon.cfg"
            pass
        else:
            print "entree clamav non trouvee dans logmon.cfg"
            lwat=os.path.join(source,clamwat)
            put(local_path=lwat,remote_path=clamwat)
            sudo('cat /home/$SUDO_USER/clamwat >> '+x)
    else:
        print env.host, 'no watchdog config file found'

    #Run freshclam
    x=sudo('/etc/cron.daily/freshclam',warn_only=True)
    if x.return_code != 0:
        print "\033[91mFreshclam failed...\033[0m"
        return 1
    else:
    	print "\033[92mFreshclam succeeded\033[0m"

@task()
def config_clamav():
    '''Push the good configuration for CLAMAV with new PCI CLAMAV mirror'''
    if run('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        user='clamupdate'
    else:
        user='clam'

    #Push configuration files with good rights and specific user depending os version
    lscan=os.path.join(source,freshclam)
    put(local_path=lscan, remote_path='/etc/freshclam.conf',use_sudo=True,mode=0700)
    sudo('''sed -i 's/DatabaseOwner/DatabaseOwner '''+user+'''/g' /etc/freshclam.conf''')
    sudo('chown root: /etc/freshclam.conf')
    lscan=os.path.join(source,freshdaily)
    put(local_path=lscan, remote_path='/etc/cron.daily/freshclam',use_sudo=True,mode=0700)
    sudo('''sed -i 's/clam.clam/'''+user+''':'''+user+'''/g' /etc/cron.daily/freshclam''')
    sudo('chown root: /etc/cron.daily/freshclam')
    lscan=os.path.join(source,freshrotate)
    put(local_path=lscan, remote_path='/etc/logrotate.d/freshclam',use_sudo=True,mode=0644)
    sudo('''sed -i 's/clam clam/'''+user+''' '''+user+'''/g' /etc/logrotate.d/freshclam''')
    sudo('chown root: /etc/logrotate.d/freshclam')
    clamcron=StringIO.StringIO( ('%02d %02d * * sun   root    /usr/local/etc/clamscan &> /dev/null\n')%(random.randint(0,59),random.randint(6,12)))
    put(clamcron,'/etc/cron.d/clamscan',use_sudo=True,mode=0600)
    sudo('chown root: /etc/cron.d/clamscan')
    if run("hostname | grep sips",quiet=True):
        lscan=os.path.join(source,clamscansips)
    else:
        lscan=os.path.join(source,clamscan)
    put(local_path=lscan, remote_path='/usr/local/etc/clamscan',use_sudo=True,mode=0700)
    sudo('chown root: /usr/local/etc/clamscan')
    if not exists('/var/lib/clamav', use_sudo=True):
        sudo('mkdir -p /var/lib/clamav')
    sudo('chown -R '+user+':'+user+' /var/lib/clamav')
    if exists('/var/log/freshclam.log', use_sudo=True):
        sudo('chown '+user+':'+user+' /var/log/freshclam.log')
    if not exists('/var/log/clamav', use_sudo=True):
        sudo('mkdir -p /var/log/clamav')
    sudo('chown -R '+user+':'+user+' /var/log/clamav')
    if exists('/var/lib/clamav/mirrors.dat', use_sudo=True):
        sudo('rm /var/lib/clamav/mirrors.dat')
    if exists('/usr/share/doc/clamav-0.*/signatures.pdf', use_sudo=True):
        sudo('rm /usr/share/doc/clamav-0.*/signatures.pdf')
    x=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    if ( x != "None"):
        if sudo("grep -P '/var/log/clamav/clamscan.log' "+x,quiet=True):
            pass
        else:
            lwat=os.path.join(source,clamwat)
            put(local_path=lwat,remote_path=clamwat)
            sudo('cat /home/$SUDO_USER/clamwat >> '+x)
    else:
        print env.host, 'no watchdog config file found'

    #Run freshclam
    x=sudo('/etc/cron.daily/freshclam',warn_only=True)
    if x.return_code != 0:
        print "\033[91mFreshclam failed...\033[0m"
        return 1
    else:
        print "\033[92mFreshclam succeeded\033[0m"


@task()
def freshclam_clamav():
    ''' run freshclam and check if succeeded '''
    if exists('/etc/cron.daily/freshclam', use_sudo=True):
    	#Run freshclam
    	x=sudo('/etc/cron.daily/freshclam',warn_only=True)
    	if x.return_code != 0:
        	print "\033[91mFreshclam failed...\033[0m"
        	return 1
    	else:
        	print "\033[92mFreshclam succeeded\033[0m"

@task()
def check_freshclam_clamscan():
    ''' check if freshclam and clamscan process are running '''
    run = '0'
    if sudo('ps -ef | grep -i freshclam | grep -v grep',quiet=True).succeeded:
    	print "\033[91mFreshclam running...\033[0m"
	run = '1'
    if sudo('ps -ef | grep -i clamscan | grep -v grep',quiet=True).succeeded:
        print "\033[91mClamscan running...\033[0m"
        run = '1'
    if run == '1':
	x=sudo('yum info installed clamav | grep Version',warn_only=True,quiet=True)
	print "\033[91mClamAV "+x+"\033[0m"
        x=sudo('cat /etc/redhat-release',warn_only=True,quiet=True)
        print "\033[91m"+x+"\033[0m"

@task()
def fix_clamscan():
    ''' fix cron clamscan '''
    if exists('/etc/cron.d/clamscan', use_sudo=True):
    	x=sudo('grep /dev/null /etc/cron.d/clamscan',warn_only=True,quiet=True)
        if x.succeeded:
    		print "\033[96mClamscan cron file already fix\033[0m"
    	else:
                x=sudo('''sed -i 's/nul/null/g' /etc/cron.d/clamscan''',warn_only=True,quiet=True)
    		if x.succeeded:
    			print "\033[92mClamscan cron file has been fixed\033[0m"
    		else:
    			print "\033[91mUnable to fix clamscan cron file...\033[0m"
    else:
	print "\033[91mClamscan file not found...\033[0m"
        return 1

@task()
def which_clamav():
    ''' find clamav version '''
    x=sudo('rpm -qa  |grep -i clamav',warn_only=True)
    if x.succeeded:
        print ':-:',x,';',env.host
    else:
        print ':-:notfound ;',env.host

@task()
def check_mirror_clamav():
    ''' check if last clamav mirror is set '''
    if exists('/etc/freshclam.conf', use_sudo=True):
        x=sudo('grep freshclam.priv.atos.fr /etc/freshclam.conf',warn_only=True,quiet=True)
        if x.succeeded:
                print "\033[91mOld ClamAV mirror !!!\033[0m"
    else:
        print "\033[91mFreshclam file not found...\033[0m"

@task()
def config_rsyslog():
    ''' configure rsyslog (if needed) and restart his service'''
    x=first('/etc/rsyslog.d/50_remote.conf','/etc/rsyslog.conf')
    if ( x != "None"):
    	if sudo("grep -P 'syslog-pci-mutv|new-syslog-pci-mutv' "+x,quiet=True):
		print "\033[96mRsyslog is configured properly\033[0m"
    	else:
		print "\033[91mRsyslog is not configured properly\033[0m"	
    elif exists('/etc/rsyslog.d/50_remote.conf_NONPCI', use_sudo=True):
    	if sudo("grep -P 'syslog-pci-mutv|new-syslog-pci-mutv' /etc/rsyslog.d/50_remote.conf_NONPCI",quiet=True):
    		sudo("mv /etc/rsyslog.d/50_remote.conf_NONPCI /etc/rsyslog.d/50_remote.conf",quiet=True)
    		sudo("service rsyslog restart",quiet=True)
    		print "\033[92mRsyslog has been configured and restarted\033[0m"
    	else:
    		print "\033[91mRsyslog is not configured properly...\033[0m"
    else:
    	print "\033[91m No Rsyslog configuration file found\033[0m"




@task()
def auditd_conf_c6():
    ''' push auditd rules conf for Centos 6 '''
    lscan=os.path.join(source,auditdconfc6)
    put(local_path=lscan, remote_path='/etc/audit/audit.rules',use_sudo=True,mode=0755)

@task()
def auditd_conf_c6_light():
    ''' push light auditd rules conf for Centos 6 (BDD,Cluster) '''
    lscan=os.path.join(source,auditdconfc6light)
    put(local_path=lscan, remote_path='/etc/audit/audit.rules',use_sudo=True,mode=0755)
    if sudo('service auditd restart',quiet=True).succeeded:
    	print "\033[92mAuditD service has been restarted (6)\033[0m"
    else:
    	print "\033[91mProblem when restarting AuditD service (6)\033[0m"

@task()
def auditd_conf_c7():
    ''' push auditd rules conf for Centos 7 '''
    lscan=os.path.join(source,auditdconfc7)
    put(local_path=lscan, remote_path='/etc/audit/rules.d/audit.rules',use_sudo=True,mode=0755)

@task()
def check_size_auditd_files():
    ''' check auditd file size '''
    if exists('/etc/audit/rules.d/audit.rules', use_sudo=True):
    	x=sudo('''ls -l /etc/audit/rules.d/audit.rules''',warn_only=True,quiet=True)
	print x
    if exists('/etc/audit/audit.rules', use_sudo=True):
        x=sudo('''ls -l /etc/audit/audit.rules''',warn_only=True,quiet=True)
	print x

@task()
def fix_auditd_syslog_plugin():
    ''' enable syslog plugin and restart auditd '''
    if exists('/etc/audisp/plugins.d/syslog.conf', use_sudo=True):
        x=sudo('''grep -sqiE '^active' /etc/audisp/plugins.d/syslog.conf''',warn_only=True,quiet=True)
        if x.succeeded:
                x=sudo('''sed -ri 's/^active.*/active = yes/g' /etc/audisp/plugins.d/syslog.conf''',warn_only=True,quiet=True)
                if x.succeeded:
                        print "\033[92mSyslog plugin has been defined to 'yes'\033[0m"
                else:
                        print "\033[91mUnable to define Syslog plugin to 'yes'\033[0m"
        else:
                sudo('echo "active = yes" >> /etc/audisp/plugins.d/syslog.conf',warn_only=True,quiet=True)
                print "\033[92mSyslog plugin has been added and defined to 'yes'\033[0m"
        x=sudo('service auditd restart',warn_only=True,quiet=True)
        if x.succeeded:
                print "\033[92mAuditD service has been restarted successfully\033[0m"
        else:
                print "\033[91mAuditD service did not restart properly\033[0m"
    else:
        print "\033[91mSyslog.conf file not found...\033[0m"
        return 1


@task()
def fix_ssh_access():
   ''' set PasswordAuthentification and PermitRootLogin to 'no' '''
   needrestart = 0
   x=first('/usr/local/openssh/etc/sshd_config','/etc/ssh/sshd_config')
   if ( x != "None"):
   	if sudo("sshd -T | grep -e '^passwordauthentication yes'",quiet=True):
		sudo('''sed -ri 's/#?PasswordAuthentication.*yes/PasswordAuthentication no/g' '''+x,quiet=True)
   		needrestart = 1
		print "\033[92mPasswordAuthentification has been set to 'no'\033[0m"
   	if sudo("sshd -T | grep -e '^permitrootlogin yes'",quiet=True):
        	sudo('''sed -ri 's/#?PermitRootLogin.*yes/PermitRootLogin no/g' '''+x,quiet=True)
        	needrestart = 1
        	print "\033[92mPermitRootLogin has been set to 'no'\033[0m"
   	if needrestart == 1:
   		x=sudo("service sshd restart",warn_only=True,quiet=True)
		if x.succeeded:
   			print "\033[92mSSHD service restarted\033[0m"
   		else:
   			print "\033[91mFailed to restart SSHD\033[0m"
   	else:
   		print "\033[96mSSHD is correctly set\033[0m"
   else:
   	print "\033[91mNo SSHD configuration file found\033[0m"

@task()
def del_signatures_pdf():
    ''' delete /usr/share/doc/clamavXXXX/signatures.pdf '''
    sudo('rm /usr/share/doc/clamav-0.97.?/signatures.pdf',warn_only=True)

@task()
def add_umask():
    ''' add umask 027 in /etc/profile.d/pci.sh '''
    pciprofile='/etc/profile.d/pci.sh'
    if exists(pciprofile, use_sudo=True):
        if sudo('''grep -sqiE '^umask 027' '''+pciprofile ,quiet=True).succeeded:
                print "\033[96mUmask is already set to 027\033[0m"
        elif sudo('''grep -sqiE '^umask.*' '''+pciprofile ,quiet=True).succeeded:
                sudo('''sed -ri 's/^umask.*/umask 027/g' '''+pciprofile,quiet=True)
                print "\033[92mUmask has been modified to 027\033[0m"
        else:
                sudo('echo umask 027 >> '+pciprofile,quiet=True)
                print "\033[92mUmask has been defined to 027\033[0m"
    else:
        sudo('echo umask 027 >> '+pciprofile,quiet=True)
        print "\033[92mUmask has been defined to 027 (pci.sh created)\033[0m"

@task()
def check_rpm_awl():
    ''' check awl-ccsrch package '''
    x=sudo('rpm -qa | grep -i awl-ccsrch',warn_only=True)
    if x.succeeded:
    	print "\033[92mPackage awl-ccsrch found\033[0m"
    else:
    	print "\033[91mPackage awl-ccsrch not found\033[0m"

@task()
def check_connect():
    ''' teste que la connexion ssh est OK '''
    sudo('echo $HOME')

@task()
def push_ntp_for_vdm_mut_pci():
    ''' push NTP file adapated for VENDOME mutalized PCI machines '''
    script = 'ntp.conf.for.mutu.vdm.pci'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    sudo('mv /home/$SUDO_USER/ntp.conf.for.mutu.vdm.pci /etc/ntp.conf')
    state.output.everything = True
    sudo("service ntpd restart",warn_only=False,quiet=False)
    time.sleep(2)
    sudo("ntpq -p",warn_only=False,quiet=False)

@task()
def push_ntp_for_scl_mut_pci():
    ''' push NTP file adapated for SECLIN mutalized PCI machines '''
    script = 'ntp.conf.for.mutu.scl.pci'
    lscript=os.path.join(source,script)
    put(local_path=lscript, remote_path=script, mode=0755)
    sudo('mv /home/$SUDO_USER/ntp.conf.for.mutu.scl.pci /etc/ntp.conf')
    state.output.everything = True
    sudo("service ntpd restart",warn_only=False,quiet=False)
    time.sleep(2)
    sudo("ntpq -p",warn_only=False,quiet=False)

@task()
def yum_repolist():
    """Launch yum repolist command"""
    state.output.everything = True
    sudo('yum repolist',warn_only=False,quiet=False)

@task()
def check_logmon_size():
    '''check the size of logmon.cfg'''
    x=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    if ( x != "None"):
        lines=sudo('''wc -l '''+x,quiet=True)
	print env.host+'\t'+lines
    else:
        print '\033[91mNo watchdog config file found !\033[0m'

@task()
def check_watchdog_logmon_var_log_messages():
    '''check how many times File /var/log/messages is defined in logmon.conf'''
    x=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    if ( x != "None"):
        #state.output.everything = True
        lines=sudo('''grep 'File /var/log/messages' '''+x + ''' | grep -v '#' | wc -l ''',warn_only=True,quiet=True)
        print env.host+'\t'+lines
    else:
        print '\033[91mNo watchdog config file found !\033[0m'
 
@task()
def check_watchdog_logmon_apply_syst_patches():
    '''display where is located apply_system_patche lines in logmon.conf'''
    x=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    if ( x != "None"):
        lines=sudo('''grep -b5 'WARNING_APPLY_PATCHES_SYSTEM' '''+x + ''' | grep -v 'ERROR' ''',warn_only=True,quiet=True)
	if "/var/log/messages" not in lines:
        	print '\033[91mProblem with line /var/log/messages\n\n'+lines+'\033[0m'
    else:
        print '\033[91mNo watchdog config file found !\033[0m'



def check_new_dns_main(future_dns_1, future_dns_2):
    ''' partie principale des scripts de check d'access DNS'''
    state.output.everything = True

    #print "future DNS 1: "+future_dns_1
    #print "future DNS 2: "+future_dns_2

    # initialisation
    echec_dns = "0"

    # check du serveur DNS1 host prive
    lines=sudo('''dig @'''+future_dns_1+''' opsurv01v.priv.atos.fr A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'
    # check du serveur DNS1 host public
    lines=sudo('''dig @'''+future_dns_1+''' www.google.com A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'

    # check du serveur DNS2 host prive
    lines=sudo('''dig @'''+future_dns_2+''' opsurv01v.priv.atos.fr A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'


    # check du serveur DNS2 host public
    lines=sudo('''dig @'''+future_dns_2+''' www.google.com A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'


    # lancement de l'upgrade du /etc/resolv.conf (si aucun echec)
    if echec_dns == "1":
        print env.host+' - \033[91mLes nouveaux DNS ne sont pas accessibles !\033[0m'
        print '-------------------------------'
    else:
         print env.host+' - \033[92mLes nouveaux DNS sont utilisables\033[0m'


@task()
def check_new_dns_nsXX_fr_vdm():
    '''check that the server can use the ns01-fr.vdm.vmbfi.svc.meshcore.net DNS to resolv'''
    future_dns_1 = "10.72.87.253"
    future_dns_2 = "10.72.87.254"
    check_new_dns_main(future_dns_1, future_dns_2)

@task()
def check_new_dns_nsXX_be_vdm():
    '''check that the server can use the ns01-fr.vdm.vmbfi.svc.meshcore.net DNS to resolv'''
    future_dns_1 = "10.72.173.251"
    future_dns_2 = "10.72.173.252"
    check_new_dns_main(future_dns_1, future_dns_2)

@task()
def check_new_dns_nsXX_be_scl():
    '''check that the server can use the ns01-be.scl.vmbfi.svc.meshcore.net DNS to resolv'''
    future_dns_1 = "10.34.242.21"
    future_dns_2 = "10.34.242.22"
    check_new_dns_main(future_dns_1, future_dns_2)


@task()
def check_new_dns_nsXX_fr_scl():
    '''check that the server can use the ns01-fr.scl.vmbfi.svc.meshcore.net DNS to resolv'''
    future_dns_1 = "10.34.234.253"
    future_dns_2 = "10.34.234.254"
    check_new_dns_main(future_dns_1, future_dns_2)

@task()
def check_new_dns_nsXX_sp_scl():
    '''check that the server can use the ns01-sp.scl.vmbfi.svc.meshcore.net DNS to resolv'''
    future_dns_1 = "10.34.181.225"
    future_dns_2 = "10.34.181.226"
    check_new_dns_main(future_dns_1, future_dns_2)



def update_resolv_conf_main(future_dns_1, future_dns_2, ancien_dns_1, ancien_dns_2):
    ''' partie principale des scripts d'update de resolv.conf'''
    print "future_dns_1 : "+future_dns_1
    print "future_dns_2 : "+future_dns_2
    print "ancien_dns_1 : "+ancien_dns_1
    print "ancien_dns_2 : "+ancien_dns_2

    state.output.everything = True
    #initialisation variable
    echec_dns = "0"
    # check du serveur DNS1 host prive
    lines=sudo('''dig @'''+future_dns_1+''' opsurv01v.priv.atos.fr A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'

    # check du serveur DNS1 host public
    lines=sudo('''dig @'''+future_dns_1+''' www.google.com A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'

    # check du serveur DNS2 host prive
    lines=sudo('''dig @'''+future_dns_2+''' opsurv01v.priv.atos.fr A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'


    # check du serveur DNS2 host public
    lines=sudo('''dig @'''+future_dns_2+''' www.google.com A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
    #print env.host+'\t'+lines
    if lines == '0':
        #print env.host+'\033[91m DNS1 KO !\033[0m'
        echec_dns = "1"
    #else:
        #print env.host+'\t DNS1 OK'


    # lancement de l'upgrade du /etc/resolv.conf (si aucun echec)
    if echec_dns == "1":
        print env.host+' - \033[91mLes nouveaux DNS ne sont pas accessibles, pas d upgrade du /etc/resolv.conf !\033[0m'
        print '-------------------------------'
    else:

        # sauvegarde fichier /etc/resolv.conf avant modif
        if not exists('/tmp/resolv.conf_2218989', use_sudo=True):
                sudo('''cp -p /etc/resolv.conf /tmp/resolv.conf_2218989''',warn_only=True,quiet=True)

        print env.host+' - Upgrade du /etc/resolv.conf '
       # update serveur DNS1
        sudo('''sed -i s/'nameserver\W*'''+ancien_dns_1+''''/'nameserver '''+future_dns_1+''''/ /etc/resolv.conf''',warn_only=True,quiet=False)
        # update serveur DNS2
        sudo('''sed -i s/'nameserver\W*'''+ancien_dns_2+''''/'nameserver '''+future_dns_2+''''/ /etc/resolv.conf''',warn_only=True,quiet=False)


        # Affichage des lignes nameserv pour verification
        sudo('''grep nameserver /etc/resolv.conf''',warn_only=True,quiet=False)


        # Test d'une resolution de nom
        lines=sudo('''dig www.google.com A +noall +answer | grep -v -e '^$' | grep -v ';' | wc -l ''',warn_only=True,quiet=True)
        #print env.host+'\t'+lines
        if lines == '0':
            print env.host+' - \033[91mLA RESOLUTION DNS NE MARCHE PLUS !\033[0m'
            print '-------------------------------'
        else:
            print env.host+' - \033[92mRESOLUTION OK\033[0m'
            print '-------------------------------'



@task()
def update_resolv_conf_to_nsXX_fr_scl():
    '''update /etc/resolv.conf in SECLIN to use nsXX-fr.scl.vmbfi.svc.meshcore.net '''
    future_dns_1 = "10.34.234.253"
    future_dns_2 = "10.34.234.254"
    ancien_dns_1 = "10.25.165.187"
    ancien_dns_2 = "10.25.165.188"
    update_resolv_conf_main(future_dns_1, future_dns_2, ancien_dns_1, ancien_dns_2)

@task()
def update_resolv_conf_to_nsXX_fr_vdm():
    '''update /etc/resolv.conf in VENDOME to use nsXX-fr.vdm.vmbfi.svc.meshcore.net '''
    future_dns_1 = "10.72.87.253"
    future_dns_2 = "10.72.87.254"
    ancien_dns_1 = "10.18.75.187"
    ancien_dns_2 = "10.18.75.188"
    update_resolv_conf_main(future_dns_1, future_dns_2, ancien_dns_1, ancien_dns_2)

@task()
def update_resolv_conf_to_nsXX_be_vdm():
    '''update /etc/resolv.conf in VENDOME to use nsXX-be.vdm.vmbfi.svc.meshcore.net '''
    future_dns_1 = "10.72.173.251"
    future_dns_2 = "10.72.173.252"
    ancien_dns_1 = "10.18.75.187"
    ancien_dns_2 = "10.18.75.188"
    update_resolv_conf_main(future_dns_1, future_dns_2, ancien_dns_1, ancien_dns_2)

@task()
def update_resolv_conf_to_nsXX_be_scl():
    '''update /etc/resolv.conf in SECLIN to use nsXX-be.scl.vmbfi.svc.meshcore.net '''
    future_dns_1 = "10.34.242.21"
    future_dns_2 = "10.34.242.22"
    ancien_dns_1 = "10.25.165.187"
    ancien_dns_2 = "10.25.165.188"
    update_resolv_conf_main(future_dns_1, future_dns_2, ancien_dns_1, ancien_dns_2)

@task()
def update_resolv_conf_to_nsXX_sp_scl():
    '''update /etc/resolv.conf in SECLIN to use nsXX-sp.scl.vmbfi.svc.meshcore.net '''
    future_dns_1 = "10.34.181.225"
    future_dns_2 = "10.34.181.226"
    ancien_dns_1 = "10.25.165.187"
    ancien_dns_2 = "10.25.165.188"
    update_resolv_conf_main(future_dns_1, future_dns_2, ancien_dns_1, ancien_dns_2)

@task()
def watchdog_temporary_local():
    '''put temporary watchdog to local for 4 hours'''
    state.output.everything = True
    sudo('wat -local 240',warn_only=True,quiet=False)

@task()
def watchdog_remote():
    '''put watchdog to remote mode'''
    state.output.everything = True
    sudo('wat -remote',warn_only=True,quiet=False)

@task()
def watchdog_stop():
    '''stop watchdog '''
    state.output.everything = True
    sudo('wat -stop',warn_only=True,quiet=False)

@task()
def watchdog_start():
    '''start watchdog '''
    state.output.everything = True
    sudo('wat -start',warn_only=True,quiet=False)

@task()
def watchdog_who():
    '''perform a watchdog -who '''
    state.output.everything = True
    sudo('wat -who',warn_only=True,quiet=False)

@task()
def crond_stop():
    '''stop crond '''
    #state.output.everything = True
    x=sudo('service crond stop',warn_only=True,quiet=False)
    if x.succeeded:
                print "\033[92mcrond service has been stoped successfully\033[0m"
    else:
                print "\033[91mcrond service did not stop properly\033[0m"

@task()
def crond_start():
    '''start crond '''
    #state.output.everything = True
    x=sudo('service crond start',warn_only=True,quiet=False)
    if x.succeeded:
                print "\033[92mcrond service has been started successfully\033[0m"
    else:
                print "\033[91mwarning - crond service did not start properly !!!!!\033[0m"
@task()
def check_git_uninstall():
    '''Check git uninstall'''
    gitcheck=sudo('grep -iE "Erase.*git" /var/log/yum.log*',quiet=True)
    print '[ \033[96m'+gitcheck+'\033[0m ]'

@task()
def check_openssh():
    '''Check OpenSSH version (AWL or not)'''
    x=run('cat /etc/redhat-release',quiet=True)
    print '\033[96m'+x+'\033[0m'
    openssh=sudo('rpm -qa | grep openssh | grep -vE "clients|server|ldap"',quiet=True)
    if "awl-openssh" in openssh:
        print "\033[91mBad OpenSSH version : "+openssh+"\033[0m"
    elif "openssh" in openssh:
        print "\033[92mGood OpenSSH version : "+openssh+"\033[0m"
    else:
        print "No root privileges..."

@task()
def upgrade_openssh_for_c6():
    '''Remove awl-openssh* and install openssh* packages for secure ciphers'''
    VERSION_OS=sudo('''rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1''',quiet=True)
    gitstate = ''
    if not VERSION_OS == "6":
        print "[ \033[95mNo valid OS version found ("+VERSION_OS+"), must be Redhat or CentOs 6\033[0m ]"
        return 1
    if sudo('rpm -q awl-openssh',quiet=True).failed:
        print '[ \033[96mOpenSSH is already in good version !\033[0m ]'
        return 1
    if sudo('yum list available openssh-clients',quiet=True).succeeded:
        print "[ \033[92mOpenSSH packages available\033[0m ]"
    else:
        print "[ \033[91mOpenSSH packages not available !\033[0m ]"
        return 1
    if sudo('rpm -q git',quiet=True).succeeded:		
    	gitstate = 'present'
    	print "[ \033[93mGit will be uninstalled during openssh upgrade and will be reinstalled immediately afterwards.\033[0m ]"
    excludeline=sudo('''grep -iE '^exclude.*' /etc/yum.conf''',quiet=True)
    if excludeline.succeeded:
        if sudo('''grep -iE '^exclude.*awl-openssh' /etc/yum.conf''',quiet=True).succeeded:
                print '[ \033[96mawl-openssh* exclusion already present in /etc/yum.conf\033[0m ]'
        else:
                if sudo('''sed -i 's/^'''+excludeline+'''/'''+excludeline+''' awl-openssh\*/g' /etc/yum.conf''').succeeded:
                        print "[ \033[92mawl-openssh* exclusion added in /etc/yum.conf (Line modified)\033[0m ]"
                else:
                        print "[ \033[91mUnable to add awl-openssh* exclusion in /etc/yum.conf\033[0m ]"
                        return 1
    else:
        if sudo('echo "exclude=awl-openssh*" >> /etc/yum.conf',quiet=True).succeeded:
                print "[ \033[92mawl-openssh* exclusion added in /etc/yum.conf\033[0m ]"
        else:
                print "[ \033[91mUnable to add awl-openssh* exclusion in /etc/yum.conf\033[0m ]"
                return 1

    if not exists('/tmp/sshd_config.bak', use_sudo=True):
        if sudo('cp -pf /etc/ssh/sshd_config /tmp/sshd_config.bak',quiet=True).succeeded:
                print "[ \033[92msshd_config file was saved in /tmp\033[0m ]"
        else:
                print "[ \033[91mUnable to save sshd_config file in /tmp\033[0m ]"
                return 1
    else:
        print '[ \033[96msshd_config file already saved in /tmp\033[0m ]'

    oldopenssh=sudo('rpm -qa |grep awl-openssh|xargs -Ixx rpm -q xx --qf "%{name} "',quiet=True)
    newopenssh=sudo('rpm -qa |grep awl-openssh|xargs -Ixx rpm -q xx --qf "%{name} "|sed "s/awl-//g"',quiet=True)
    if newopenssh.succeeded:
    	if gitstate == 'present':
    		newopenssh += 'git'    	
        state.output.everything = True
        sudo('yum remove -y '+oldopenssh)
        sudo('yum install -y '+newopenssh)
    else:
        print '[ \033[91mUnable to defined new OpenSSH packages\033[0m ]'
        return 1
    if gitstate == 'present':
    	if sudo('rpm -q git',quiet=True).succeeded:
		print "[ \033[92mGit was successfully reinstalled.\033[0m ]"
	else:
		print "[ \033[91mUnable to reinstall Git !\033[0m ]"
    if sudo('cp -pf /tmp/sshd_config.bak /etc/ssh/sshd_config',quiet=True).succeeded:
        print "[ \033[92msshd_config backup was restored\033[0m ]"
    else:
        print "[ \033[91mUnable to restore sshd_config backup !\033[0m ]"
        return 1
    time.sleep(1)
    sudo('/sbin/service sshd stop && /sbin/service sshd start',quiet=True)
    if sudo('/sbin/service sshd status',quiet=True).succeeded:
        print "[ \033[92mSSHD service was restarted successfully\033[0m ]"
    else:
        if sudo('echo -e "*/1 * * * * root /sbin/service sshd restart && rm -f /etc/cron.d/restartsshd" > /etc/cron.d/restartsshd',quiet=True).succeeded:
                print "[ \033[92mRestart of SSHD service was scheduled in crontab (Execution in less than a minute)\033[0m ]"
        else:
                print "[ \033[91mUnable to properly restart SSHD service and schedule it in cron !\033[0m ]"


def replaceline(match,new,base,fileconfig):
    '''Find and replace cipher/macs/keys, if not found, add it above "base" variable'''
    if sudo('''grep -qiE '''+match+''' '''+fileconfig,quiet=True).succeeded:
        sed(fileconfig,before=match,after=new,use_sudo=True,flags="i")
    else:
        if sudo('''grep -qiE ^'''+base+''' '''+fileconfig,quiet=True).succeeded:
                sed(fileconfig,before='^'+base,after=new+'\\n'+base,use_sudo=True,flags="i")
        else:
                print "\033[91mUnable to found "+base+"\033[0m"
                sys.exit(1)

@task()
def set_sshd_cipher():
    ''' Set ciphers, MACs and KEX allowed in sshd config '''
    VERSION_OS=sudo('''rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1''',quiet=True)
    if not VERSION_OS > "5":
        print "\033[95mNo valid OS version found ("+VERSION_OS+"), must be Redhat or CentOs 6 or 7\033[0m"
        return 1
    else:
        if VERSION_OS == "6":
            if sudo('rpm -q awl-openssh',quiet=True).succeeded:
                print '[ \033[91mOpenSSH has bad version !\033[0m ]'
                return 1
            if not exists('/tmp/sshd_config.bak', use_sudo=True):
                if sudo('cp -pf /etc/ssh/sshd_config /tmp/sshd_config.bak',quiet=True).succeeded:
                        print "[ \033[92msshd_config file was saved in /tmp\033[0m ]"
                else:
                        print "[ \033[91mUnable to save sshd_config file in /tmp\033[0m ]"
                        return 1
            newciphers='''Ciphers aes256-ctr,aes192-ctr,aes128-ctr'''
            newmacs='''MACs hmac-sha2-512,hmac-sha2-256'''
            newkex='''KexAlgorithms diffie-hellman-group-exchange-sha256'''
        else:
            newciphers='''Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr'''
            newmacs='''MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,hmac-sha2-512,hmac-sha2-256'''
            newkex='''KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256'''
        if VERSION_OS > "6":
                restart='/bin/systemctl restart sshd.service'
                config='/etc/ssh/sshd_config'
        else:
                y=sudo('basename $(ls -1 /etc/init.d/*|grep ssh)',quiet=True)
                x=y.splitlines()[-1]
                if x in ("sshd","opensshd"):
                        if ( x == "opensshd"):
                                restart='/sbin/service '+x+' status'
                                config='/usr/local/openssh/etc/sshd_config'
                        else:
                                restart='/sbin/service '+x+' status'
                                config='/etc/ssh/sshd_config'
                else:
                        print "\033[91mError : No valid SSHD\033[0m"
                        return 1
        oldm=sudo('''grep -iE "^Protocol\W+2" '''+config,quiet=True)
        if oldm.failed:
                print "\033[91mProtocol 2 not found in "+config+" !\033[0m"
                return 1
        replaceline("^KexAlgorithms .*",newkex,oldm,config)
        replaceline("^MACs .*",newmacs,newkex,config)
        replaceline("^Ciphers .*",newciphers,newmacs,config)

        #Match fix
        if VERSION_OS == "7":
                if sudo('grep -iE "^Match" '+config,quiet=True).failed:
                        AKC=sudo('''grep -iE "^AuthorizedKeysCommand\W+.*" '''+config,quiet=True)
                        if AKC.failed:
                                print "\033[91mAuthorizedKeysCommand not found in "+config+" !\033[0m"
                                return 1
                        replaceline("^#Match .*","Match                           Address 10.26.238.33,10.26.238.34,10.50.238.33,10.82.238.33,10.26.238.61,10.26.238.62,127.0.0.1",AKC,config)
        if VERSION_OS == "6":
                sudo('/sbin/service '+x+' stop && /sbin/service '+x+' start',quiet=True)
        if sudo(restart,quiet=True).succeeded:
                print "[ \033[92mSSHD service was restarted successfully\033[0m ]"
        else:
                if sudo('echo -e "*/1 * * * * root /sbin/service sshd restart && rm -f /etc/cron.d/restartsshd" > /etc/cron.d/restartsshd',quiet=True).succeeded:
                        print "[ \033[92mRestart of SSHD service was scheduled in crontab (Execution in less than a minute)\033[0m ]"
                else:
                        print "[ \033[91mUnable to properly restart SSHD service and schedule it in cron !\033[0m ]"

@task()
def restore_sshd_config():
    ''' Restore SSHD config backup in /etc/ssh/, if not exist disable Ciphers/MAC/KEX '''
    VERSION_OS=sudo('''rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1''',quiet=True)
    if not VERSION_OS > "5":
        print "\033[95mNo valid OS version found ("+VERSION_OS+"), must be Redhat or CentOs 6 or 7\033[0m"
        return 1

    if exists('/tmp/sshd_config.bak', use_sudo=True):
        if sudo('cp -pf /tmp/sshd_config.bak /etc/ssh/sshd_config',quiet=True).succeeded:
                print "[ \033[92msshd_config file was restored\033[0m ]"
        else:
                print "[ \033[91mUnable to restore sshd_config file\033[0m ]"
                return 1
    else:
        sed('/etc/ssh/sshd_config',before='^Ciphers .*',after='',use_sudo=True)
        sed('/etc/ssh/sshd_config',before='^MACs .*',after='',use_sudo=True)
        sed('/etc/ssh/sshd_config',before='^KexAlgorithms .*',after='',use_sudo=True)
        print "[ \033[92mCiphers/MAC/KEX have been disabled\033[0m ]"

    if VERSION_OS == "6":
        sudo('/sbin/service sshd stop && /sbin/service sshd start',quiet=True)
        restart='/sbin/service sshd status'
    else:
        restart='/bin/systemctl restart sshd.service'

    if sudo(restart,quiet=True).succeeded:
            print "[ \033[92mSSHD service was restarted successfully\033[0m ]"
    else:
            if sudo('echo -e "*/1 * * * * root /sbin/service sshd restart && rm -f /etc/cron.d/restartsshd" > /etc/cron.d/restartsshd',quiet=True).succeeded:
                    print "[ \033[92mRestart of SSHD service was scheduled in crontab (Execution in less than a minute)\033[0m ]"
            else:
                    print "[ \033[91mUnable to properly restart SSHD service and schedule it in cron !\033[0m ]"
