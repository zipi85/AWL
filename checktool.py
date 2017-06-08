from pipes import quote

from fabric.api import sudo, settings, task
from fabric import state

from fabric.operations import put, require
from fabric.contrib.files import exists as file_exists, contains, append, sed

from lib.user import delete as delete_user
from lib.rpm import is_installed as rpm_is_installed

# Hide Fabric output
# state.output.status   = False
# state.output.aborts   = False
# state.output.warnings = False
# state.output.running  = True
# state.output.sudo     = True
# state.output.stdout   = False
# state.output.stderr   = False
# state.output.user     = False

# Hiding everything
state.output.everything = False
state.output.running  = True


def remove_awl_audit_tools():
    """
    Remove awl-audit-tools, audit-tools
    Must be use only for migrate or it will remove checktoolV2 too.
    """

    # Removing all rpms about awl-audit-tool or audit-tools
    sudo("yum -y remove audit-tools awl-audit-tool nagios* checktool* nrpe*")

    # Deleting old config file for awl-audit-tool
    sudo('rm -rf /usr/local/nagios')

    # Delete users
    delete_user("nagios")
    delete_user("nrpe")


@task()
def install():
    """install checktoolV2"""

    if rpm_is_installed('checktoolV2-nrpe'):
        update()
    else:
        sudo("yum install -y --enablerepo=awl-main repositories-chkt")
        sudo("yum install -y --enablerepo=epel,chkt-main checktoolV2-nrpe")


@task()
def remove():
    """remove checktoolV2"""
    sudo("yum remove -y --enablerepo=epel,chkt-main checktoolV2-*")


@task()
def update():
    """update checktoolV2"""
    sudo("yum -y update --enablerepo=epel,chkt-main checktoolV2-*")


@task()
def migrate():
    """migrate from awl-audit-tool to checktoolV2"""
    remove_awl_audit_tools()
    install()

@task()
def install_nrpe():
    """install nrpe"""
    sudo("yum install -y --enablerepo=epel nrpe")

@task()
def new_plugins():
    """push new plugins"""
    # copie du fichier de definition des services/plugins
    put('/srv/awl_bfi_fabric/data/checktool/commands_pci.cfg', '/etc/nrpe.d/commands_pci.cfg', use_sudo=True, mode=0644)
    sudo('chown root:root /etc/nrpe.d/commands_pci.cfg')
    # copie des plugins corriges
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd_rules.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_tripwire-aide.sh', '/usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh', use_sudo=True, mode=0755)
    # Application des droits pour les plugins corriges
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh')
    # Relance du service nrpe
    if sudo('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        sudo("systemctl restart nrpe.service")
    else:
        sudo("service nrpe reload")

@task()
def update_plugin_l_pci_auditd_rules():
    """push the latest version of l_pci_auditd_rules plugin"""
    # copie des plugins corriges
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd_rules.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh', use_sudo=True, mode=0755)
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh')

@task()
def update_plugin_l_pci_yumupdate():
    """push the latest version of l_pci_umask yum_update"""
    # copie des plugins corriges
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_yumupdate.sh', '/usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh', use_sudo=True, mode=0755)
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')

@task()
def update_plugin_l_pci_umask():
    """push the latest version of l_pci_umask plugin"""
    # copie des plugins corriges
    put('/srv/awl-bfi-fabric-git/data/checktool/l_pci_umask.sh', '/usr/lib/checktoolV2/plugins/l_pci_umask.sh', use_sudo=True, mode=0755)
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_umask.sh')

@task()
def fix_plugins_3():
    """fix plugin umask and yum update"""
    # copie des plugins corriges
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_umask.sh', '/usr/lib/checktoolV2/plugins/l_pci_umask.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_yumupdate.sh', '/usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh', use_sudo=True, mode=0755)
    # Application des droits pour les plugins corriges
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_umask.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')

@task()
def fix_plugins_2():
    """run some fix plugins"""
    # copie des plugins corriges
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_ssh_access.sh', '/usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_yumupdate.sh', '/usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_rsyslog.py', '/usr/lib/checktoolV2/plugins/l_rsyslog.py', use_sudo=True, mode=0755)

    # Application des droits pour les plugins corriges
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_rsyslog.py')

@task()
def fix_plugins_1():
    """run some fix plugins"""
    # copie des plugins corriges
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_clamav.sh', '/usr/lib/checktoolV2/plugins/l_pci_clamav.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_yumupdate.sh', '/usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_rsyslog.sh', '/usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_ssh_access.sh', '/usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd.sh', use_sudo=True, mode=0755)

    # Application des droits pour les plugins corriges
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_clamav.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd.sh')

    sed('/etc/nagios/nrpe.cfg',before='dont_blame_nrpe=1',after='dont_blame_nrpe=0', use_sudo=True, backup='.bak', flags='', shell=False)

    # relance du service nrpe
    if sudo('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        x=sudo("systemctl restart nrpe.service")
        if x.succeeded:
                print 'NRPE service restarted'
        else:
                print 'NRPE service failed'
    else:
        x=sudo("service nrpe reload")
        if x.succeeded:
                print 'NRPE service reloaded'
        else:
                print 'NRPE service failed'

@task()
def dev_update():
    """update a checktoolV2 client with developement environment"""
    # install or update nrpe
    if rpm_is_installed('nrpe'):
        sudo("yum -y update nrpe --enablerepo=epel")
    else:
        sudo("yum install -y --enablerepo=epel nrpe")

    # install or update rpm checktoolV2-*
    if rpm_is_installed('checktoolV2-nrpe'):
        sudo("yum -y update --enablerepo=epel,chkt-main checktoolV2-*")
    else:
        sudo("yum install -y --enablerepo=awl-main repositories-chkt")
        sudo("yum install -y --enablerepo=epel,chkt-main checktoolV2-nrpe")

    # set dont_blame_nrpe=1
    sed('/etc/nagios/nrpe.cfg',before='dont_blame_nrpe=1',after='dont_blame_nrpe=0', use_sudo=True, backup='.bak', flags='', shell=False)

    # copie du fichier de definition des services/plugins
    put('/srv/awl_bfi_fabric/data/checktool/commands_pci.cfg', '/etc/nrpe.d/commands_pci.cfg', use_sudo=True, mode=0644)
    sudo('chown root:root /etc/nrpe.d/commands_pci.cfg')
    # copie des plugins
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_clamav.sh', '/usr/lib/checktoolV2/plugins/l_pci_clamav.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_timeout.sh', '/usr/lib/checktoolV2/plugins/l_pci_timeout.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_umask.sh', '/usr/lib/checktoolV2/plugins/l_pci_umask.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_yumupdate.sh', '/usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_blame_nrpe.sh', '/usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_su.sh', '/usr/lib/checktoolV2/plugins/l_pci_su.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/check_ntpdate', '/usr/lib/checktoolV2/plugins/check_ntpdate', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_uptime.pl', '/usr/lib/checktoolV2/plugins/l_uptime.pl', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_ssh_access.sh', '/usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_rsyslog.sh', '/usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_rsyslog.py', '/usr/lib/checktoolV2/plugins/l_rsyslog.py', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd_rules.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_tripwire-aide.sh', '/usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh', use_sudo=True, mode=0755)
# Application des droits sur les plugins
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_clamav.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_timeout.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_umask.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_su.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/check_ntpdate')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_uptime.pl')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_rsyslog.py')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh')
# relance du service nrpe
    if sudo('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        sudo("systemctl restart nrpe.service")
    else:
        sudo("service nrpe reload")

@task()
def dev_update_without_nrpe():
    """update a checktoolV2 client with developement environment BUT without update/install nrpe or checktoolV2-nrpe """

    # set dont_blame_nrpe=1
    sed('/etc/nagios/nrpe.cfg',before='dont_blame_nrpe=1',after='dont_blame_nrpe=0', use_sudo=True, backup='.bak', flags='', shell=False)

    # copie du fichier de definition des services/plugins
    put('/srv/awl_bfi_fabric/data/checktool/commands_pci.cfg', '/etc/nrpe.d/commands_pci.cfg', use_sudo=True, mode=0644)
    sudo('chown root:root /etc/nrpe.d/commands_pci.cfg')
    # copie des plugins
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_clamav.sh', '/usr/lib/checktoolV2/plugins/l_pci_clamav.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_timeout.sh', '/usr/lib/checktoolV2/plugins/l_pci_timeout.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_umask.sh', '/usr/lib/checktoolV2/plugins/l_pci_umask.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_yumupdate.sh', '/usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_blame_nrpe.sh', '/usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_su.sh', '/usr/lib/checktoolV2/plugins/l_pci_su.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/check_ntpdate', '/usr/lib/checktoolV2/plugins/check_ntpdate', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_uptime.pl', '/usr/lib/checktoolV2/plugins/l_uptime.pl', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_ssh_access.sh', '/usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_rsyslog.sh', '/usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_auditd_rules.sh', '/usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh', use_sudo=True, mode=0755)
    put('/srv/awl_bfi_fabric/data/checktool/l_pci_tripwire-aide.sh', '/usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh', use_sudo=True, mode=0755)
# Application des droits sur les plugins
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_clamav.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_timeout.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_umask.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_su.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/check_ntpdate')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_uptime.pl')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh')
# relance du service nrpe
    if sudo('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        sudo("systemctl restart nrpe.service")
    else:
        sudo("service nrpe reload")


@task()
def dev_update_home():
    """update a checktoolV2 client with PCI environment when plugins have been already pushed to home"""

    # set dont_blame_nrpe=1
    sed('/etc/nagios/nrpe.cfg',before='dont_blame_nrpe=1',after='dont_blame_nrpe=0', use_sudo=True, backup='.bak', flags='', shell=False)

    # warning, all plugins must have been pushed previously to the server's home directory

    # deplacement des fichiers de definition
    sudo("mv commands_pci.cfg /etc/nrpe.d/commands_pci.cfg")
    sudo("mv l_pci_clamav.sh /usr/lib/checktoolV2/plugins/l_pci_clamav.sh")
    sudo("mv l_pci_timeout.sh /usr/lib/checktoolV2/plugins/l_pci_timeout.sh")
    sudo("mv l_pci_umask.sh /usr/lib/checktoolV2/plugins/l_pci_umask.sh")
    sudo("mv l_pci_yumupdate.sh /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh")
    sudo("mv l_pci_auditd.sh /usr/lib/checktoolV2/plugins/l_pci_auditd.sh")
    sudo("mv l_pci_blame_nrpe.sh /usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh")
    sudo("mv l_pci_su.sh /usr/lib/checktoolV2/plugins/l_pci_su.sh")
    sudo("mv check_ntpdate /usr/lib/checktoolV2/plugins/check_ntpdate")
    sudo("mv l_uptime.pl /usr/lib/checktoolV2/plugins/l_uptime.pl")
    sudo("mv l_pci_ssh_access.sh /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh")
    sudo("mv l_pci_rsyslog.sh /usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh")
    sudo("mv l_pci_auditd_rules.sh /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh")
    sudo("mv l_pci_tripwire-aide.sh /usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh")

    # chang droits sur fichiers plugin
    sudo("chmod 0755 /etc/nrpe.d/commands_pci.cfg")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_clamav.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_timeout.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_umask.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_auditd.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_su.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/check_ntpdate")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_uptime.pl")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh")
    sudo("chmod 0755 /usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh")

    # chown sur plugins
    sudo('chown root:root /etc/nrpe.d/commands_pci.cfg')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_clamav.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_timeout.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_umask.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_yumupdate.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_blame_nrpe.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_su.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/check_ntpdate')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_uptime.pl')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_ssh_access.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_rsyslog.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_auditd_rules.sh')
    sudo('chown root:root /usr/lib/checktoolV2/plugins/l_pci_tripwire-aide.sh')

# relance du service nrpe
    if sudo('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        sudo("systemctl restart nrpe.service")
    else:
        sudo("service nrpe reload")

@task()
def set_dont_blame_to_0():
    """update /etc/nagios/nrpe.cfg and replace the value 1 to value 0 in field dont_blame_nrpe"""
    sed('/etc/nagios/nrpe.cfg',before='dont_blame_nrpe=1',after='dont_blame_nrpe=0', use_sudo=True, backup='.bak', flags='', shell=False)

    # relance du service nrpe
    if sudo('''cat /etc/redhat-release | grep 'release 7' ''',quiet=True):
        sudo("systemctl restart nrpe.service")
    else:
        sudo("service nrpe reload")
