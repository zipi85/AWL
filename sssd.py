import os
import sys
import time
import getpass

from fabric.api import *
from fabric.operations import put, require
from fabric.contrib.files import contains, append, sed, upload_template
from awl_bfi_fabric.conf.settings import DATA_DIR

# source files
source = os.path.join(DATA_DIR, 'sssd')
sssd_tar = 'sssd.tar'

# the user installing sssd should be the one testing the connection
username = getpass.getuser()

def is_rpm_installed(rpm):
    """Query a rpm"""
    result = sudo(('rpm -q %s') % (rpm), warn_only=True)
    return result

def install_rpm(rpm):
    """Install a rpm"""
    result = sudo(('yum install -y %s') % (rpm) )
    return result

def update_sshd_iam():
    """update sshd config to add IAM requirements"""
    sshd_match=[]
    sshd_match.append('Match                           Address 10.26.238.33,10.26.238.34,10.50.238.33,10.82.238.33,10.26.238.61,10.26.238.62')
    sshd_match.append('        AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys')
    sshd_match.append('        AuthorizedKeysCommandRunAs root')
   
    append('/etc/ssh/sshd_config', (sshd_match), use_sudo=True)

def install_sssd():
    print "Starting install_sssd for %s" % env.host
    sudo('echo %s > /usr/local/give_access_users' % username)

    if (is_rpm_installed('sssd').failed):
        install_rpm('sssd')
    
    if (is_rpm_installed('libsss_sudo').failed):
        install_rpm('libsss_sudo')
    
    mytar = os.path.join(source, sssd_tar)
    mytarR = os.path.join('/tmp/', sssd_tar)
    
    put(local_path=mytar, remote_path=mytarR, mode=0644)
    sudo(('tar -xvPf %s')% (mytarR))
    sudo('chkconfig sssd on')

@task()
def install_iam(secdom=None, token=False):
    """Connect a server to NIM/IAM

	:param secdom: security domain, see output of the command
	               `sudo /usr/local/security/bin/Update_SecDOM -list' on gateway-fr

	:param token: use RSA token to authenticate the connection
    """

    if not secdom:
    	abort("Expected argument secdom")

    # pass env as dict to template
    env.secdom = secdom

	# select the template for sssd.conf
    if token:
		source_conf = os.path.join(source, 'sssd.conf.token')
    else:
    	source_conf = os.path.join(source, 'sssd.conf')

    install_sssd()
    dest = '/etc/sssd/sssd.conf'
    upload_template(source_conf, dest, context=env, mode=0600,use_sudo=True)
    sudo(('chown root:root %s') % (dest))

    update_sshd_iam()
    sudo('service sssd start')
    result = sudo ('getent passwd %s' % username) 
    print "%s %s" % (result ,env.host)
    time.sleep(2)

    result = sudo('sudo -lU %s' % username)
    print result
    time.sleep(2)

    sudo('service sssd restart')
    time.sleep(2)

    result = sudo('sudo -lU %s' % username)
    print result
    time.sleep(2)
    
    sudo('service sshd reload')
    time.sleep(2)
    
    result = sudo('service sshd status', warn_only=True)
    print result
    print "sssd successfully installed -hopefully- on %s " % (env.host)

