from fabric.api import task, hide, sudo
import fabric.contrib.files
from fabric.contrib.files import exists, contains, append, first, sed

@task()
def update():
    """update itdiscovery"""
    with hide('stdout', 'stderr'):
    	sudo('yum -y update itdiscovery --enablerepo=awl-main,epel')

@task()
def remove_pci_option():
	"""remove `-P` option from cron file"""
	with hide('stdout', 'stderr'):
		fabric.contrib.files.sed('/etc/cron.d/itdiscovery', '-P', '', use_sudo=True, backup='')

@task()
def upgrade_v3():
        """upgrade ITDiscovery v3"""
        with hide('stdout', 'stderr'):
                if exists('/etc/cron.d/itdiscovery', use_sudo=True):
			smtp=sudo('''grep -o -E '(ypp|relay-smtp|smtp).*fr|relay-smtp' /etc/cron.d/itdiscovery''',warn_only=True,quiet=True)
			if smtp.succeeded:
				print "\033[95m"+smtp+"\033[0m"
				installitdisc=sudo("yum -y update itdiscovery --enablerepo=awl-main,epel",quiet=True)
				if installitdisc.succeeded:
                                        print "\033[92mITDiscovery has been installed successfully\033[0m"
                                else:
                                        print "\033[91mFailed to install ITDiscovery\033[0m"
					return 1
				sudo('''sed -ri 's/#?smtp_server:.*/smtp_server: '''+smtp+'''/g' /etc/itdiscovery/itdiscovery.yml''',quiet=True)
				ittest=sudo("itdiscovery -W",quiet=True)
				if ittest.succeeded:
					print "\033[92mITDiscovery is correctly set\033[0m"
				else:
					print "\033[91mProblem with ITDiscovery\033[0m"
					return 1
			else:
				itdiscv3=sudo('''grep nice /etc/cron.d/itdiscovery''',warn_only=True,quiet=True)
				if itdiscv3.succeeded:
					print "\033[96mITDiscovery V3 already installed.\033[0m"
				else:
					print "\033[93mNo SMTP found in ITDiscovery cron.\033[0m"
		else:
			print "\033[91mITDiscovery cron not found\033[0m"
	
