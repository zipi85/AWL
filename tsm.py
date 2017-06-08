import os.path
import socket
from netaddr import *

from fabric.api import *
from fabric.contrib import *
from fabric.contrib.files import *
from fabric.operations import put, require
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR, DATA_DIR
from awl_bfi_fabric.lib import filesystem
from fabric import state

source = os.path.join(DATA_DIR, 'tsm')

def check_ip_data():
    """
    check if ip data is mounted
    """
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        ping = run('ping -c 1 -t 1 '+env.host+'.data')
    return ping.return_code

def set_ip_data():
    """
    set ip data conf
    """
    ipdata = get_ip_data()
    prompt("Interface :", key='appinterface', default='eth1')
    #check if interface exist
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        ifconfig = sudo('/sbin/ifconfig '+env.appinterface)
    if ifconfig.return_code != 0:
        print '[ \033[91mKO\033[0m ] '+env.appinterface+' not found'
        return 1

    prompt("Netmask :", key='appnetmask', default='255.255.255.0')

    # create dict to render the template
    d = dict(
        interface = env.appinterface,
        ip = ipdata,
        netmask = env.appnetmask
        )

    template = os.path.join(TEMPLATE_DIR, 'tsm', 'ifcfg-eth')
    dest = '/etc/sysconfig/network-scripts/ifcfg-'+env.appinterface
    upload_template(template, dest, context=d, use_sudo=True, mode=0644)
    sudo('chown root:root '+dest)

    # upload route config
    gateway = IPNetwork(ipdata+'/'+env.appnetmask)
    d = dict(
        gateway=gateway[1]
        )

    template = os.path.join(TEMPLATE_DIR, 'tsm', 'route-eth')
    dest = '/etc/sysconfig/network-scripts/route-'+env.appinterface
    upload_template(template, dest, context=d, use_sudo=True, mode=0644)
    sudo('chown root:root '+dest)
    sudo('/sbin/ifdown '+env.appinterface)
    sudo('/sbin/ifup '+env.appinterface)
    return 0

def get_ip_data():
    """
    get ip data
    """
    return socket.gethostbyname(env.host+'.data')

def check_dns():
    """
    check dns and reverse dns
    """
    try:
        ipdata = get_ip_data()
    except Exception:
        print "[ \033[91mKO\033[0m ] DNS IP DATA"
        return 1
    else:
        print "[ \033[92mOK\033[0m ] DNS IP DATA"
    try:
        socket.gethostbyaddr(ipdata)
    except Exception:
        print "[ \033[91mKO\033[0m ] REVERSE DNS IP DATA"
        return 0
    else:
        print "[ \033[92mOK\033[0m ] REVERSE DNS IP DATA"
        return 0

def install_rpm_tsm():
    """
    install tivoli repositorie and rpm
    """
    sudo('yum install -y repositories-tivoli.noarch --enablerepo=awl-main')
    sudo('yum install -y br-tsmcli.noarch --enablerepo=tivoli-main,tivoli-external')
    sudo('yum install -y tsmcli-adm.noarch --enablerepo=tivoli-main,tivoli-external')
    sudo('yum install -y tsmcli-menu.noarch --enablerepo=tivoli-main,tivoli-external')
    sudo('yum install -y --enablerepo=awl-main repositories-tws')
    sudo('yum install -y --enablerepo=awl-main repositories-secure')
    sudo('yum install -y --enablerepo=awl-main repositories-inner')
    sudo('yum install -y --disablerepo=\* --enablerepo=tws*,secure*,inner* tws-ea.noarch')
    return 0

def create_fs():
    """
    create FS : /opt/tivoli/tsm /opt/backup/tsmcli /etc/backup/tsmcli /var/log/backup
    """
    prompt("volum group (minimum required : 2,1Go) :", key='appvgname', default='vgappli')
    print("\033[93mAttention :\n\tcentos/rhel 5/6 : ext3\n\tcentos/rhel 7 : ext4 \033[0m")
    prompt("Filesystem type :", key='appfstype', default='ext4')
    append('/etc/fstab', '', use_sudo=True)
    append('/etc/fstab', '# TSM', use_sudo=True)
    filesystem.create('/opt/tivoli/tsm', '1G',vgname=env.appvgname, user='root', group='root', type=env.appfstype)
    filesystem.create('/opt/backup/tsmcli', '50m',vgname=env.appvgname, user='root', group='root', type=env.appfstype)
    filesystem.create('/etc/backup/tsmcli', '50m',vgname=env.appvgname, user='root', group='root', type=env.appfstype)
    filesystem.create('/var/log/backup', '1G',vgname=env.appvgname, user='root', group='root', type=env.appfstype)
    return 0

def create_user():
    """
    create user/group maestro
    """
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        group = sudo('id -g maestro')
    if group.return_code !=0:
        sudo('groupadd -g 500 maestro')
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        user = sudo('id -u maestro')
    if user.return_code !=0:
        sudo('useradd -g 500 -u 500 -d /home/maestro -c "TWS Owner" maestro')
    return 0

def add_ssh_keys():
    """
    Add SSH Keys for maestro user
    """
    if env.host[1] == 'p':
        prompt("Compliancy domain [PCI of NOPCI] :", key='appcompliancy', default='PCI')
        if env.appcompliancy == 'PCI':
            env.sshkey = 'from="10.34.88.146,10.34.88.147,10.72.12.173,10.72.12.174",command="/usr/local/bin/SshRestrict.pl TWS" ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAzHU1WMLxFGohFdnUHkFtrzmMYg2/Secx8yhABILsQhUZ5EorVSAiz9HRl5/jXzyhwJOoB/t1PVi3gtGy00Ivgqu5/OnSDi+syohxIFPN6VVfV7nhbTuTntbRMzKJmUUIYgRrhwXtsQhcIgqt8+MlZ9UwXdOKGb0GlXoCu1WQRSusy095GAEH/EOLPGQZkMxzNILO6pmNApBSSgPjKUaIomWO0yTs8ep5KEcJc7swqGRgt/8w9t7yZwbrzMfK/U5yjBeM9InH9G7MRoBosRynG6RPUk9HnNmX9aLCPSoA0/6R2QcugHyL0V52ra9CIKxePelWlRcclSVeVXPk8UXSBQ== maestro@opurs001s/002s/001v/002v'
        else:
            env.sshkey = 'from="10.34.116.18,10.34.116.19,10.18.250.45,10.18.250.46",command="/usr/local/bin/SshRestrict.pl TWS" ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq8lPEYZv4kbWkr8FQYQ6YE50qZC+L1c/HEP0Nyfhr9kNb9yRuqGgYU0BW/x9Ty91WuoNlWqXW41TnykrTImiEbMFB/jd0qmszkFz8paFMBTY/sEAQ2fQKptA17/P/wGx9wlOe+c4PpPqpvjDASBV1mB3g+ChBWEC7rQn+haht27MnAVXaqw4eiWTFDGEPPsWPYncj5Qn1/en1nuojvzWsXzO/kAl+rXg2fA4ynaWzW0nnGUR+NU3ehQ1nekQCT2QuKTq9P3KeP1LbnH1gczRhnbQblg3CQgG6e+QaBKZqTJriaBjPP9OmvYHInW/R6eb0QYK4CqQrWi0E1Ob+g17wQ== maestro@tpurs001s/002s/001v/002v'
    else:
        print '[ \033[91mKO\033[0m ] XA is installed for applicative usage, or in TWS qualif environment, please asked TWS Support Team rights FTAs\nBackup Support can indicate rights FTAs to use (depending on PCI or NON-PCI constraints).'
        prompt("SSH key :", key='sshkey')

    sudo('mkdir -p ~maestro/.ssh')
    sudo('chown maestro:maestro ~maestro/.ssh')
    sudo('chmod 700 ~maestro/.ssh')
    if not exists('/path/to/remote/file', use_sudo=True):
        sudo('touch ~maestro/.ssh/authorized_keys')
    sudo('chown maestro:maestro ~maestro/.ssh/authorized_keys')
    sudo('chmod 644 ~maestro/.ssh/authorized_keys')
    append('~maestro/.ssh/authorized_keys', env.sshkey, use_sudo=True)
    return 0

@task
def install():
    """
    install tsm requirements
    """
    if check_dns() != 0:
        return 1
    """if check_ip_data() != 0:
        if set_ip_data() != 0:
        return 1"""
    create_user()
    create_fs()
    install_rpm_tsm()
    add_ssh_keys()
    print('\033[93m Ask network admin team, firewall opening FROM FTAs hosts, TO extended agents, on TCP 22 port \033[0m')


def verif_scl_tsm_prereq():
    ''' run specific script to check the TSM prerequirements in Seclin '''

    # test lookup
    y=sudo('nslookup spspci21s')
    if y.succeeded:
        print 'nslookup: OK'
    else:
        print 'nslookup: KO   !!!!'

    # test de la route
    x=sudo('''netstat -rn | grep 10.28.112.0''',warn_only=True,quiet=True)
    if x.succeeded:
         print 'route to TSM: OK'
    else:
         print 'route to TSM: KO   !!!!'


    # test de la connexion
    x=sudo('''perl -MIO::Socket -e '$socket=IO::Socket::INET->new(Proto=>tcp,PeerAddr=>$ARGV[0],PeerPort=>$ARGV[1],Timeout=>2);if($@) { exit 1 } else { exit 0; }' spspci21s.data.priv.atos.fr 1500''',warn_only=True,quiet=True)
    if x.succeeded:
         print 'access to TSM: OK'
    else:
         print 'access to TSM: KO   !!!!'


@task
def verif_vdm_tsm_prereq():
    ''' run specific script to check the TSM prerequirements in Vendome '''

    # test lookup
    y=sudo('nslookup spspci31v')
    if y.succeeded:
        print 'nslookup: OK'
    else:
        print 'nslookup: KO   !!!!'

    # test de la route
    x=sudo('''netstat -rn | grep 10.20.36.0''',warn_only=True,quiet=True)
    if x.succeeded:
         print 'route to TSM: OK'
    else:
         print 'route to TSM: KO   !!!!'


    # test de la connexion
    x=sudo('''perl -MIO::Socket -e '$socket=IO::Socket::INET->new(Proto=>tcp,PeerAddr=>$ARGV[0],PeerPort=>$ARGV[1],Timeout=>2);if($@) { exit 1 } else { exit 0; }' spspci31v.data.priv.atos.fr 1500''',warn_only=True,quiet=True)
    if x.succeeded:
         print 'access to TSM: OK'
    else:
         print 'access to TSM: KO   !!!!'

@task()
def script_fix():
    '''Push tsmcli_migration.sh script and allow tsmadm to run it'''
    tsmpath='/opt/tivoli/tsm/client/ba/bin/'
    tsmscript='tsmcli_migration.sh'
    tsmsudoers='/etc/sudoers.d/tsmadm'
    if not exists(tsmpath, use_sudo=True):
        if sudo('mkdir -p '+tsmpath,warn_only=True,quiet=True).succeeded:
                print '[ \033[92mDirectory '+tsmpath+' created\033[0m ]'
        else:
                print '[ \033[91mUnable to create directory : '+tsmpath+'\033[0m ]'
                return 1
    lscan=os.path.join(source,tsmscript)
    if put(local_path=lscan, remote_path=tsmpath+tsmscript,use_sudo=True,mode=0754).succeeded:
        sudo('chown root:root '+tsmpath+tsmscript,quiet=True)
        print '[ \033[92mThe script '+tsmscript+' has been pushed\033[0m ]'
    else:
        print '[ \033[91mUnable to push '+tsmscript+'\033[0m ]'
        return 1

    if sudo('grep -sqi '+tsmpath+tsmscript+' '+tsmsudoers,quiet=True).succeeded:
                print '[ \033[96mtsmadm already has the rights to run '+tsmscript+'\033[0m ]'
    else:
                if sudo('echo "tsmadm,%UsrSave ALL=(root) NOPASSWD: "'+tsmpath+tsmscript+' | (EDITOR="tee -a" visudo -f '+tsmsudoers+')',warn_only=True,quiet=True).succeeded:
                        print '[ \033[92mtsmadm now has the rights to run '+tsmscript+'\033[0m ]'
                else:
                        print '[ \033[91mUnable to write line in '+tsmsudoers+'\033[0m ]'
                        return 1
