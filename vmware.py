from fabric.api import task, hide, sudo
from fabric.contrib.files import exists as file_exists


@task
def update_vmware_tools_51():
    """update the VMware tools"""

    with hide('stdout', 'stderr'):
        # update rpm
        sudo('yum -y --enablerepo=vmware-5.1 update vmware-tools-esx-nox')

        # bug vmware-tools : rename the library libtimeSync.so
        #   http://communities.vmware.com/thread/423709?start=0&tstart=0
        #   http://www.chriscolotti.us/vmware/workaround-for-vsphere-5-1-guest-unable-to-collect-ipv4-routing-table/
        bug_file = '/usr/lib/vmware-tools/plugins/vmsvc/libtimeSync.so'
        bug_rename = '/usr/lib/vmware-tools/plugins/vmsvc/libtimeSync.so-'
        if file_exists(bug_file):
            sudo('mv %s %s' % (bug_file, bug_rename))

