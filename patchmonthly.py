import os.path
from io import StringIO

from fabric.api import *
from fabric.colors import yellow
from fabric.contrib.files import exists as file_exists
from fabric.contrib.files import append

from awl_bfi_fabric.lib.utils import run_as_root, upload
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR
from awl_bfi_fabric.lib.system import get_distrib_version
#import awl_bfi_fabric.repos as repos

import dataset


@runs_once
def load_table_patchxpress():
	"""return the content of the table patchxpress"""

	# connect to the database
	db = dataset.connect('mysql://fabric:LJjK4hffNBjUabx3@localhost:3306/YPBFIBDD1')
	table_patchxpress = db['patchxpress_advance_monthly']
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
    #        sudo cannot be use anymore until the correction is made.
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
    # execute(repos.deploy_all)


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

