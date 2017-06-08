import os.path

from lvm import lvcreate
from disk import mkfs, tune2fs, mount, add_fstab
from files import is_dir
from utils import run_as_root

def create(mountpoint, size, vgname="vgappli", user='root', group='root', permissions='0755', type='ext4'):
    """
    Create a filesystem 
    """
    # As a rule, we change `/' to `_' in the lvname and omit the first one.
    # We also replace `-' by `_' or else device mapper change it to `--'
    lvname = '_'.join(mountpoint.split('/')[1:]).replace('-', '_')
    device = os.path.join('/dev', vgname, lvname)
    dm = os.path.join('/dev/mapper/', '-'.join([vgname, lvname]))

    lvcreate(lvname, size, vgname)
    # Pass dm as arg because mkfs() check if the device is already mount
    # parsing the output of `mount` command and LVM partition are listed
    # with their device mapper. 
    mkfs(dm, type)    
    tune2fs(dm)

    if not is_dir(mountpoint):
        run_as_root('umask 0022 && mkdir -p %(mountpoint)s' % locals())

    mount(device, mountpoint)
    add_fstab(device, mountpoint, type)

    # setup permissions
    run_as_root('chown %(user)s:%(group)s %(mountpoint)s' % locals())
    run_as_root('chmod %(permissions)s %(mountpoint)s' % locals())








