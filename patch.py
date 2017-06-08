import os.path
import socket
from io import StringIO

from fabric.api import *
from fabric.colors import red, cyan, green, yellow
from fabric.contrib.files import exists as file_exists
from fabric.contrib.files import append, first
from fabric import state

from awl_bfi_fabric.lib.utils import run_as_root, upload
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR
from awl_bfi_fabric.lib.system import get_distrib_version
import awl_bfi_fabric.repos as repos

import dataset


@runs_once
def load_table_patchxpress():
	"""return the content of the table patchxpress"""

	# connect to the database
	db = dataset.connect('mysql://fabric:LJjK4hffNBjUabx3@localhost:3306/YPBFIBDD1')
	table_patchxpress = db['patchxpress']
	return table_patchxpress


def upload_cron(table_patchxpress):
    """create cron file and upload it"""

    # search hostname in the table patchxpress
    rows = table_patchxpress.find(HOST=env.host)
    content = []

    # there can be several definition for one host
    for row in rows:
    	line = "%(CRONTAB_ACTIF)s%(CRONTAB_MINUTES)s %(CRONTAB_HEURES)s %(CRONTAB_JOUR_MOIS)s %(CRONTAB_MOIS)s %(CRONTAB_JOUR_SEMAINE)s %(CRONTAB_BINAIRE)s %(REBOOT)s %(WARNING_PILOTAGE)s %(CRONTAB_TRACE)s \n" % row
        content.append(line)

    if content:
    	# create an in-memory file object and delivers it on host
    	print content
    	src = StringIO("\n".join(content))
    	dst = '/etc/cron.d/apply_system_patches'
    	upload(src, dst, use_sudo=True, mode=0600)
    else:
    	# a planing must exists in patchxpress, but we want to be able to upload the shells anyway
    	print yellow('%s does not exist in patchxpress, do not upload crontab' % env.host)


def upload_dependencies(table_patchxpress):
    """create dependencie file and upload it"""

    # search hostname in the table patchxpress
    row = table_patchxpress.find_one(HOST=env.host)
    if row:
    	content = "%(CHECK_HOSTS)s \n" % row
    	# create an in-memory file object and delivers it on host
    	src = StringIO(content)
    	dst = '/etc/apply_system_patches.dependencies'
    	upload(src, dst, use_sudo=True, mode=0600)
    else:
    	# a planing must exists in patchxpress but we want to be able to upload the shells anyway
    	print yellow('%s does not exist in patchxpress, do not upload dependencies' % env.host)

@task()
def push_only_ASP_script():
    """push only /usr/local/bin/apply_system_patches script to the latest vesion"""

    # upload shell
    src = os.path.join(TEMPLATE_DIR, 'patch', 'apply_system_patches')
    dst = '/usr/local/bin/apply_system_patches'
    upload(src, dst, use_sudo=True, mode=0700)

@task()
def upload_shell():
    """upload apply_system_patches shell to manage patches and reboot"""

    # upload shell
    src = os.path.join(TEMPLATE_DIR, 'patch', 'apply_system_patches')
    dst = '/usr/local/bin/apply_system_patches'
    upload(src, dst, use_sudo=True, mode=0700)

    # upload disable shell
    src = os.path.join(TEMPLATE_DIR, 'patch', 'DISABLE_apply_system_patches')
    dst = '/usr/local/bin/DISABLE_apply_system_patches'
    upload(src, dst, use_sudo=True, mode=0700)

    # upload enable shell
    src = os.path.join(TEMPLATE_DIR, 'patch', 'ENABLE_apply_system_patches')
    dst = '/usr/local/bin/ENABLE_apply_system_patches'
    upload(src, dst, use_sudo=True, mode=0700)

    # touch /etc/apply_system_patches.LAUNCH
    append('/etc/apply_system_patches.LAUNCH', 'True', use_sudo=True)

    # upload sudoers permissions
	# RHEL5: If the permissions of a file under /etc/sudoers.d/ are wrong,
    #        /sudo cannot be use anymore until the correction is made.
	#        the files ending with a `~' or `.' character are ignore.
	# RHEL6: A message is shown and the commands in the file are not made available
	#        but it doesn't stop our script
    src = os.path.join(TEMPLATE_DIR, 'patch', 'manage_patches')
    if get_distrib_version().startswith('5'):
    	tmp = '/etc/sudoers.d/manage_patches~'
    	dst = '/etc/sudoers.d/manage_patches'
    	upload(src, tmp, use_sudo=True, mode=0440)
    	sudo('mv %s %s' % (tmp, dst))
    else:
    	dst = '/etc/sudoers.d/manage_patches'
    	upload(src, dst, use_sudo=True, mode=0440)

    # upload post-update for RHEL5
    if get_distrib_version().startswith('5'):
        src = os.path.join(TEMPLATE_DIR, 'patch', 'post-update')
        dst = '/usr/local/bin/post-update'
        upload(src, dst, use_sudo=True, mode=0700)

    # upload shells that manages our repos
    execute(repos.deploy_all)


@task()
def install_patchxpress():
	"""install crontab and its dependencies to patch a server"""
	table_patchxpress = load_table_patchxpress()
	upload_cron(table_patchxpress)
	upload_dependencies(table_patchxpress)
	upload_shell()

@task()
def remove_cron():
	"""Remove the planification"""
	sudo('rm /etc/apply_system_patches.dependencies')
	sudo('rm /etc/cron.d/apply_system_patches')

@task()
def check_error():
        """Check errors in apply_system_patches log"""
        x=sudo('ls /var/log/apply_system_patches_*',warn_only=True,quiet=True)
        if x.return_code > 0:
        	print yellow('apply_system_patches log does not exist')
        else:
        	x=sudo('''grep -sqi 'not found' $(ls -1t /var/log/apply_system_patches_*|head -n 1)''',warn_only=True,quiet=True)
        	if x.succeeded:
        		print yellow('Error found !!!')

@task()
def check_path():
        """Check if apply_system_patches script has good path"""
        if not file_exists('/usr/local/bin/apply_system_patches', use_sudo=True):
        	print yellow('Apply_system_patches is not present !!!')
        else:
        	x=sudo('''grep -sqi 'PATH=$PATH:/sbin:/usr/sbin' /usr/local/bin/apply_system_patches''',quiet=True)	
        	if x.return_code > 0:
                	print yellow('Apply_system_patches has bad path !!!')

@task()
def check_shell():
        """Check if the apply_system_patches script is at the last version"""
        if not file_exists('/usr/local/bin/apply_system_patches', use_sudo=True):
                print yellow('ERROR - Apply_system_patches is not present !!!')
        else:
                x=sudo('''grep -sqi 'Christophe Villemont 06/01/17' /usr/local/bin/apply_system_patches''',quiet=True)
                if x.return_code > 0:
                        print yellow('ERROR - Old shell version !!!')

@task()
def check_last_log():
        """Display the last lines of the last apply_system_patches log"""
	lastfile=sudo('''ls -1t /var/log/apply_system_patches* | head -n 1''',quiet=True)
	if "No such file" not in lastfile:
        	result=sudo('tail '+lastfile)
		print yellow (result+"\n\n\n")
	else:
		print red ("No apply_system_patches log")

@task()
def sudoers_oper():
        """push sudoers file for giving rights to oper (apply_system_patches)"""
        opersudoers = '/etc/sudoers.d/oper'
        if not file_exists('/etc/sudoers.d', use_sudo=True):
                print red('/etc/sudoers.d does not exist')
                return 1
	else:
		if file_exists(opersudoers, use_sudo=True):
			sudo('> '+opersudoers,warn_only=True,quiet=True)
                append(opersudoers, 'oper,%UsrOperator ALL=(root) NOPASSWD: /usr/local/bin/apply_system_patches --reboot yes --monitoring yes', use_sudo=True)
                append(opersudoers, 'oper,%UsrOperator ALL=(root) NOPASSWD: /usr/local/bin/apply_system_patches --reboot no --monitoring no', use_sudo=True)
                append(opersudoers, 'oper,%UsrOperator ALL=(root) NOPASSWD: /bin/grep apply /var/log/messages', use_sudo=True)
                append(opersudoers, 'oper,%UsrOperator ALL=(root) NOPASSWD: /sbin/reboot', use_sudo=True)
		print green('oper sudoers file has been pushed')
	

@task()
def conf_logmon():
        """add apply_patches_system surveillance in logmon.cfg"""
    	logmon=first('/etc/watchdot/logmon.cfg','/usr/local/watch/logmon.cfg')
    	if ( logmon != "None"):
		if sudo('grep -sqi _APPLY_PATCHES_SYSTEM '+logmon,quiet=True).succeeded:
			print cyan('logmon.cfg is already configured properly')
			#return 1
		elif env.host[1] == 'p':
			append(logmon, '\n## apply_patches_system', use_sudo=True)
                	append(logmon, 'File /var/log/messages', use_sudo=True)
			append(logmon, 'WARNING_APPLY_PATCHES_SYSTEM.*Dependence  [ident=SYS-PAT-0002] [criticity=MAJ] MSG=error dependence during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Manual blocking  [ident=SYS-PAT-0002] [criticity=MAJ] MSG=error manual blocking during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_pre_control [ident=SYS-PAT-0001] [criticity=CRI] MSG=error pre_control during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_apply_patches [ident=SYS-PAT-0001] [criticity=CRI] MSG=error apply_patches during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_post_control  [ident=SYS-PAT-0001] [criticity=CRI] MSG=error post_control during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_monitoring  [ident=SYS-PAT-0001] [criticity=CRI] MSG=error monitoring during system patch management', use_sudo=True)
                	print green('logmon.cfg has been configured properly (Production)')
		else:
                	append(logmon, '\n## apply_patches_system', use_sudo=True)
                	append(logmon, 'File /var/log/messages', use_sudo=True)
			append(logmon, 'WARNING_APPLY_PATCHES_SYSTEM.*Dependence  [ident=SYS-PAT-0000] [criticity=WAR] MSG=error during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_pre_control [ident=SYS-PAT-0000] [criticity=WAR] MSG=error during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_apply_patches [ident=SYS-PAT-0000] [criticity=WAR] MSG=error during system patch management', use_sudo=True)
			append(logmon, 'ERROR_APPLY_PATCHES_SYSTEM.*Error func_post_control  [ident=SYS-PAT-0000] [criticity=WAR] MSG=error during system patch management', use_sudo=True)
                	print green('logmon.cfg has been configured properly')
	else:
                print red('No watchdog config file found !')
                return 1
	sudo('''sed -i 'N;/^\\n$/D;P;D;' '''+logmon,quiet=True)
	watcmd=first('/usr/bin/wat','/usr/local/bin/wat')
	if sudo(watcmd+' -v | grep "fhs 2"',quiet=True).succeeded:
		print red('Watchdog 2.x')
		#return 1
	if sudo(watcmd +' -local 20',quiet=True).failed:
		print red('wat local is not working')
	if run('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
		if sudo('systemctl restart watchdot.service',quiet=True).succeeded:
			print green('Watchdog service has been restarted (7)')
		else:
			print red('Problem when restarting Watchdog service (7)')
	else:
		sudo(watcmd + ' -stop',quiet=True)
                sudo('sleep 10',quiet=True)
                if sudo(watcmd + ' -start',quiet=True).succeeded:
				sudo('sleep 3',quiet=True)
			        if sudo('''ps -ef | grep -iE 'watchdot.*start' | grep -v grep''',warn_only=True,quiet=True).failed:
                			print "\033[91mWatchdog is not started !\033[0m"
				else:                        	
					print green('Watchdog service has been restarted (6)')
				sudo(watcmd +' -remote',quiet=True)
                else:
                        print red('Problem when restarting Watchdog service (6)')

@task()
def wat_remote():
      """launch wat -remote"""
      watcmd=first('/usr/bin/wat','/usr/local/bin/wat')
      state.output.everything = True
      if sudo(watcmd +' -remote',quiet=False).failed:
                print red('wat -remote is not working')
      else:
                print ('ok')

