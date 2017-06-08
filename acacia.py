from fabric.api import task, hide, sudo


@task
def update_agent():
    """update acacia-agent"""
    with hide('stdout', 'stderr'):
	sudo('yum -y --enablerepo=awl-main install repositories-acacia')
        sudo('yum -y --enablerepo=acacia-main update acacia-agent')

@task
def remove_agent():
    """remove acacia-agent"""
    with hide('stdout', 'stderr'):
        sudo('yum -y remove acacia-agent')

@task
def install_update_agent():
   "install acacia agent if not exist or update it"
   if sudo('rpm -qa | grep -i repositories-acacia',quiet=True).failed:
        if sudo('yum -y --enablerepo=awl-main install repositories-acacia',quiet=True).succeeded:
                print "\033[92mrepositories-acacia installed successfully\033[0m"
        else:
                print "\033[91mUnable to install repositories-acacia\033[0m"
   if sudo('rpm -qa | grep -i acacia-agent',quiet=True).failed:
        if sudo('yum -y --enablerepo=acacia-main,epel install acacia-agent',quiet=True).succeeded:
                print "\033[92mAcacia Agent installed successfully\033[0m"
        else:
                print "\033[91mUnable to install Acacia Agent\033[0m"
   else:
        if sudo('yum -y --enablerepo=acacia-main,epel update acacia-agent',quiet=True).succeeded:
                print "\033[92mAcacia Agent updated successfully or already up to date\033[0m"
        else:
                print "\033[91mUnable to update Acacia Agent\033[0m"
   if sudo('authconfig --passalgo=sha512 --update',quiet=True).succeeded:
        print "\033[92mpassword hashing algorithm is sha512\033[0m"
   else:
        print "\033[91mproblem for define password hashing algorithm at sha512\033[0m"
