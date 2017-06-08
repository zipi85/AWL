import os
import sys

import fabric.api
import ilogue.fexpect

from fabric.api import env, task, hide, with_settings, execute, hosts 
#from fabric.api import *
from fabric.colors import red, blue
from fabric.contrib.files import exists as file_exists
from fabric.contrib.files import contains as file_contains

from ilogue.fexpect import expect, expecting 

from fabric.operations import put

from fabric.contrib.files import upload_template
from awl_bfi_fabric.conf.settings import DATA_DIR
from lib.rpm import is_installed as rpm_is_installed

@task
@with_settings(warn_only=True)
def initdb():
    """initialize Tripwire database"""

    prompts = []

    # retrieve digits
    n = ''.join(x for x in env.host if x.isdigit())
    # reverse n and get the last 2 digits
    passwd = n[::-1][:2] + 'tripwire'

    prompts += expect('Please enter your local passphrase:', passwd)

    with expecting(prompts):
        ilogue.fexpect.sudo('/usr/local/tripwire/tfs/bin/tripwire --init')

    # cleanup
    fabric.api.run('rm /tmp/fexpect_*')


@task
@with_settings(warn_only=True)
def install():
    """install Tripwire"""

	# retrieve hostname digits
    n = ''.join(x for x in env.host if x.isdigit())

    # reverse n and get the last 2 digits
    local_passphrase = n[::-1][:2] + 'tripwire'
    site_passphrase = '00tripwire'
    
    # answers for tripwire install
    prompts = []
    prompts += expect('Please enter your site passphrase:', site_passphrase)
    prompts += expect('The local key file: \\"/usr/local/tripwire/tfs/key/local.key\\" exists. Overwrite (Y/N)?', 'Y')
    prompts += expect('Enter the local keyfile passphrase:', local_passphrase)
    prompts += expect('Verify the local keyfile passphrase:', local_passphrase)
    prompts += expect('Please enter your local passphrase:', local_passphrase)

    # get remote id and home
    Rid=fabric.api.run('id -un').splitlines()[-1]
    Rhome=fabric.api.run('pwd').splitlines()[-1]
    # upload tarball containing tripwire
    tarball = 'tripwire-pci.tgz'
    src = os.path.join(DATA_DIR, 'tripwire', tarball)
    dst = os.path.join(Rhome, tarball)
    upload_template(src, dst)

    # extract tarball
    fabric.api.run('tar zxvf %s' % dst)

    # install pexpect for dependency
    fabric.api.sudo('yum -y install pexpect')

    with expecting(prompts):
    	ilogue.fexpect.sudo(Rhome+'/tripwire-pci/install_tripwire.sh')

    if Rid !='system':
	fabric.api.sudo('chown -R system:system /usr/local/tripwire/')
   	# cleanup
    fabric.api.run('rm -rf '+Rhome+'/tripwire-pci*')
    fabric.api.run('rm /tmp/fexpect_*')


@task
@with_settings(warn_only=True)
def suivi_pci():
	"""check if Tripwire is installed and scheduled"""
	binary = "/usr/local/tripwire/tfs/bin/tripwire"
	cron_file = "/etc/cron.d/tripwire"
	cron_root = "/var/spool/cron/root"

	# just make sure the binary is present
	if file_exists(binary, use_sudo=True):
		print "%s: Tripwire is installed" % env.host
	else:
		print red("%s: Tripwire is not installed" % env.host)

	# make sure the integrity check is scheduled and active (not a comment)
	# it is scheduled with cron and the file can be either in /etc/cron.d/tripwire
	# or /var/spool/cron/root
	if (file_exists(cron_file, use_sudo=True) and
			file_contains(cron_file, '^[^#].*tripwire_check.ksh', use_sudo=True,escape=False)):
		print "%s: Tripwire is scheduled" % env.host
	elif (file_exists(cron_root, use_sudo=True) and
			file_contains(cron_root, '^[^#].*tripwire_check.ksh', use_sudo=True,escape=False)):
		print "%s: Tripwire is scheduled" % env.host
	else:
		print red("%s: Tripwire is not scheduled" % env.host)

def _un_trip():
    with fabric.api.settings(hide('running', 'status','stdout','stderr','warnings','aborts'),warn_only=True,abort_on_prompts=True):
        try:
            x=fabric.api.sudo("true",quiet=True)
            if fabric.api.sudo("ls -l /etc/redhat-release").failed:
            	print 'Warning :',env.host,' no /etc/redhat-release , skipped'
            else:
            	execute(initdb)
        except  SystemExit, e:
            print 'Warning :',env.host,' access forbidden, tripwire database wont be reinitialized '

@task()
@hosts('yppcil10v')
def reinit_tripwire_from_splunk():
    """ reinit tripwire db from splunk list of hosts with pb """
    lhosts=fabric.api.sudo("cat /opt/splunk/var/run/splunk/tripwire_epure.txt |cut -d' ' -f4|grep -v 'Status'|sort |uniq|tr '\n' ' '")
    #execute(_un_trip,hosts='opsips02s')
    execute(_un_trip,hosts=lhosts.split(' '))

@task()
@with_settings(warn_only=True)
def requirements():
    """Check requirements for Tripwire"""
    if fabric.api.sudo("grep 'release 7' /etc/redhat-release",quiet=True).succeeded:
    	print blue("This is a Centos/RedHat 7 server. Please install AIDE.")
    	return 1
    if not rpm_is_installed('glibc.*i686'):
        print red("GlibC i686 is not installed")
    if not file_exists("/usr/local/tripwire/tfs/bin/tripwire", use_sudo=True):
        print red("Tripwire is not installed")

@task()
@with_settings(warn_only=True)
def update_tripwire_check_ksh():
    """ push a new tripwire_check.ksh file"""
    source = os.path.join(DATA_DIR, 'tripwire')
    checkfile = 'tripwire_check.ksh'
    src = os.path.join(DATA_DIR, 'tripwire', checkfile)
    dst = '/usr/local/tripwire/tfs/gentrip/tripwire_check.ksh'
    
    if file_exists("/usr/local/tripwire/tfs/gentrip/tripwire_check.ksh", use_sudo=True):  
        put(local_path=src, remote_path=dst,use_sudo=True,mode=0755)
        fabric.api.sudo('chown root:root /usr/local/tripwire/tfs/gentrip/tripwire_check.ksh')
    else:
        print red("Tripwire looks to be not installed")

