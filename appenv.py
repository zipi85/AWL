import os.path

from fabric.api import *
from fabric.contrib.console import confirm
from fabric.colors import yellow

from awl_bfi_fabric.lib import user, group, lvm, disk, files, filesystem, sudoers
from awl_bfi_fabric.lib.utils import run_as_root
from awl_bfi_fabric.lib.system import get_distrib_version

# Default directories use in AWL application
DIRS = dict(
    web    = ['/WEBS', '/WEBDATA', '/WEBLOGS'],
    middle = ['/MIDDLE', '/MIDDLEDATA', '/MIDDLELOGS'],
    back   = ['/BACK', '/BACKDATA', '/BACKLOGS']
    )


def get_infos():
    """
    Get informations to build an app environment.
    """

    # The answers are stored in %env.key, prefixing them w/ 'app' to avoid conflict.
    prompt("username (mandatory) :", key='appuser')
    prompt("uid (optional) :", key='appuid')
    prompt("groupname (mandatory) :", key='appgroup', default=env.appuser)
    prompt("gid (optional) :", key='appgid', default=env.appuid)
    prompt("client (mandatory) :", key='appclient')
    prompt("application (optional) :", key='application')
    prompt("environment [f]ront [m]iddle [b]ack :", key='appenv')
    prompt("volum group :", key='appvgname', default='vgappli')
    print("\033[93mAttention :\n\tcentos/rhel 5/6 : ext3\n\tcentos/rhel 7 : ext4 \033[0m")
    prompt("Filesystem type :", key='appfstype', default='ext4')

    if "ext3" != env.appfstype.lower() and "ext4" != env.appfstype.lower():
	abort('%s is not supported.' % env.appfstype)


    # Deduce mountpoints from the answers 
    if env.appenv.lower().startswith('f'):
        arch = DIRS['web']
    elif env.appenv.lower().startswith('m'):
        arch = DIRS['middle']
    elif env.appenv.lower().startswith('b'):
        arch = DIRS['back']
    else:
        abort('%s is not supported.' % env.appenv)

    # Filesystems to create
    if env.application:
        env.mountpoint_bin  = os.path.join(arch[0], env.appclient, env.application)
        env.mountpoint_data = os.path.join(arch[1], env.appclient, env.application)
        env.mountpoint_log  = os.path.join(arch[2], env.appclient, env.application)
    else:
        env.mountpoint_bin  = os.path.join(arch[0], env.appclient)
        env.mountpoint_data = os.path.join(arch[1], env.appclient)
        env.mountpoint_log  = os.path.join(arch[2], env.appclient)

    prompt("size of %s :" % env.mountpoint_bin,  key='mountpoint_bin_size')
    prompt("size of %s :" % env.mountpoint_data, key='mountpoint_data_size')
    prompt("size of %s :" % env.mountpoint_log,  key='mountpoint_log_size')


@task
def create():
    """create an environment for an application"""

    # Ask informations to the user and store the answers in %env 
    # Since get_infos() need to be be call only once, check if env.appuser exists.
    if 'appuser' not in env:
        get_infos()
        answer = confirm("Do you wish to continue ?", default=False)
        if not answer:
            return


    # Create user and group
    if not group.exists(env.appgroup):
        group.create(env.appgroup, gid=env.appgid)
    if not user.exists(env.appuser):
        user.create(env.appuser, uid=env.appuid, group=env.appgroup)
 
    # On front, create a user w/o shell, where:
    # username = user + d ; uid = user uid + 1 ; no homedir
	if env.appenv.lower().startswith('f') and not user.exists(''.join([env.appuser,'d'])):
		if env.appuid:
			user.create(''.join([env.appuser,'d']), uid=str(int(env.appuid)+1), 
            		group=env.appgroup, shell='/sbin/nologin', create_home=False)
        else :
            user.create(''.join([env.appuser,'d']), group=env.appgroup, shell='/sbin/nologin')


    # Create filesystems only if size is defined,
    # because some might not be necessary. e.g. /WEBDATA or /WEB on filer
    if env.mountpoint_bin_size:
        filesystem.create(env.mountpoint_bin, env.mountpoint_bin_size, 
                    vgname=env.appvgname, user=env.appuser, group=env.appgroup, type=env.appfstype)
    if env.mountpoint_data_size:
        filesystem.create(env.mountpoint_data, env.mountpoint_data_size, 
                    vgname=env.appvgname, user=env.appuser, group=env.appgroup, type=env.appfstype)
    if env.mountpoint_log_size:
        filesystem.create(env.mountpoint_log, env.mountpoint_log_size, 
                    vgname=env.appvgname, user=env.appuser, group=env.appgroup, type=env.appfstype)


    # Create /etc/sudoers.d/user file only on RHEL6/C6 RHEL7/C7
	if get_distrib_version().startswith('6'):
		sudoers.app(env.appuser)
	elif get_distrib_version().startswith('7'):
		sudoers.app(env.appuser)
	else:
		print(yellow("Can't deliver the sudo file on this OS version. You have to do it manually :("))

    # Put sudo_lcmd
    if not files.is_file('/usr/local/bin/sudo_lcmd', use_sudo=True):
        sudoers.upload_sudo_lcmd()

    # When umask = 027, directories are created w/ 750 permissions,
    # forbidding app user to access theirs directories.
    # Check permissions on top directories defined in DIRS.
    dirs = []
    for key, value in DIRS.iteritems():
        for list in DIRS[key]:
            dirs.append(list)

    for dir in dirs:
        if files.is_dir(dir) and files.mode(dir) != '755':
            run_as_root('chmod 755 %s' % dir)

