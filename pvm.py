import re
import sys, os
import time
import urllib
from fabric.api import *
from fabric.operations import put, require
from fabric.contrib.files import contains, append, sed, first
from awl_bfi_fabric.conf.settings import DATA_DIR

# source files
destsource = os.path.join(DATA_DIR, 'spacewalk/')

swkeys={}
swkeys['inner']="gpg-pubkey-84017165-528b36ab"
swkeys['pvm']="gpg-pubkey-4a97d041-52527935"

keysource={}
keysource['inner']="RPM-GPG-KEY-inner"
keysource['pvm']="RPM-GPG-KEY-pvm"

#destsource="/srv/data/spacewalk/"
destcible="/tmp/"

def is_key_installed(rpm):
    """Query a rpm"""
    x=sudo(('rpm -q %s') % (rpm) ,warn_only=True )
    return x

def import_gpgkey(rpm):
    """Install a rpm"""
    x=sudo(('rpm --import %s') % (rpm) )
    return x

def install_and_disable(repo):
    sudo(("yum --enablerepo=awl-main install -y repositories-%s.noarch")%(repo))
    sed('/etc/yum.repos.d/'+repo+'.repo',before='enabled = 1',after='enabled = 0',use_sudo=True,backup='')

def _is_available(k):
    s=''
    x=sudo(("yum repolist enabled |grep -E '^(cha-.*-%s|%s-main)'") %(k,k),warn_only=True )
    if x.failed:
        y=sudo(("yum repolist disabled |grep -E '^%s-main'") %(k),warn_only=True )
        if y.failed:
            s='Unavailable'
        else: 
            s=' --enablerepo='+k+'-main '+' --enablerepo='+k+'-external '
    return s

def _yum_rpm(rpm,action,confirm):
    if rpm == '_':
        print "missing rpm"
        sys.exit(1)
    opts=''
    for k in ["inner" , "pvm"]:
        x= _is_available(k)
        if x == 'Unavailable':
            print env.host,' : Warning ',k,' Unavailable neither through repo nor Spacewalk '
        else:
            opts+=x
    yesno=''
    if confirm=='n':
        yesno=' -y '
    sudo(('yum %s %s  %s %s')%(action, yesno, opts , rpm),pty=True)

@task()
@with_settings(hide('running','debug', 'status','stdout','stderr','warnings','aborts'))
def list_gpgkeys():
    '''list all gpg public keys installed for rpm signature verification '''
    x=sudo("rpm -q gpg-pubkey --qf '%{name}-%{version}-%{release} --> %{summary}\n'")
    print x

@task()
def install_repos_keys():
    '''
        install gpg public keys for trusted repositories needed besides kickstart
        currently only pvm and inner
    '''
    for k in ["inner" , "pvm"]:
      if is_key_installed(swkeys[k]).failed:
         lp=destsource+keysource[k]
         rp=destcible+keysource[k]
         put(local_path=lp,remote_path=rp,mode=644)
         import_gpgkey(rp)
         sudo(('rm %s ')%(rp))

@task()
def set_available_trusted_sources():
    '''
        If no Spacewalk channel found for a trusted source,
           install and disable the repo
        Nothing is done if the repo is already installed or a channel exists
    '''
    install_repos_keys()
    for k in ["inner" , "pvm"]:
        if _is_available(k) =='Unavailable':
            install_and_disable(k)

@task()
def install_rpm(rpm='_',confirm='n'):
    ''' install a rpm with trusted sources enabled '''
    _yum_rpm(rpm,'install',confirm)
@task()
def update_rpm(rpm='_',confirm='n'):
    ''' updating a rpm with trusted sources enabled '''
    _yum_rpm(rpm,'update',confirm)

@task()
@with_settings(show('running','debug', 'status','stdout','stderr','warnings','aborts'))
def update_watchdot():
    ''' update watchdot to latest version, set @muteLoginuid in /etc/watchdot/watchdog.config, chkconfig and (re)start if needed '''
    set_available_trusted_sources()
    update_rpm(rpm='watchdot',confirm='n')
    if sudo('/sbin/chkconfig --list watchdot',warn_only=True).failed:
        sudo('/sbin/chkconfig --add watchdot')
    wconfig=first('/etc/watchdot/watchdog.config','/usr/local/watch/watchdog.config')
    if sudo('''grep -qE '^@muteLoginuid' '''+wconfig ,warn_only=True).failed:
        #x=sed(wconfig,'# Prefix','#@muteLoginuid to prevent auditd tracing watchdog\\n@muteLoginuid\\n&',backup='.fabric')
        mute=[]
        mute.append('#@muteLoginuid to prevent auditd tracing watchdog')
        mute.append('@muteLoginuid')
        append(wconfig,mute,use_sudo=True)
    watcmd=first('/usr/bin/wat','/usr/local/bin/wat')
    sudo(watcmd +' -stop',warn_only=True)
    time.sleep(1)
    with settings(show('running','debug', 'status','stdout','stderr','warnings','aborts')):
    	sudo(watcmd +' -start',warn_only=True)
        sudo(watcmd +' -who')
                                    
