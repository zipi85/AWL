import re

from fabric.api import hide, settings, abort
from fabric.contrib.files import append

from utils import run_as_root



def mount(device, mountpoint):
    """
    Mount a partition

    Warning : provide LVM partition w/ the following format:
              /dev/mapper/vgname-lvname

    Example::

        from lib.disk import mount

        mount('/dev/sdb1', '/mnt/usb_drive')
        mount('/dev/mapper/vg00-lv01', '/mnt/example')
    """
    if not ismounted(device):
        run_as_root('mount %(device)s %(mountpoint)s' % locals())


def ismounted(device):
    """
    Check if partition is mounted

    Example::

        from lib.disk import ismounted

        if ismounted('/dev/sda1'):
           print ("disk sda1 is mounted")
    """
    # Check filesystem
    with settings(hide('running', 'stdout')):
        res = run_as_root('mount')
    for line in res.splitlines():
        fields = line.split()
        if fields[0] == device:
            return True

    return False


def mkfs(device, ftype):
    """
    Format filesystem

    Example::

        from lib.disk import mkfs

        mkfs('/dev/sda2', 'ext4')
    """
    if not ismounted('%(device)s' % locals()):
        with settings(hide('stdout', 'warnings'), warn_only=True):
            run_as_root('mkfs.%(ftype)s %(device)s' % locals())
    else:
        abort("Partition is mounted")


def tune2fs(device, maxcounts='0', interval='0'):
    """
    Adjust filesystem parameters.
    """
    if not ismounted('%(device)s' % locals()):
        with settings(hide('stdout', 'warnings'), warn_only=True):
            run_as_root('tune2fs -c %(maxcounts)s -i %(interval)s %(device)s' % locals())
    else:
        abort("Partition is mounted")


def add_fstab(device, mountpoint, ftype='ext4', 
                options='defaults', maxcounts='0', interval='0'):
    """
    Update /etc/fstab
    """
    line = '%(device)s\t%(mountpoint)s\t%(ftype)s\t%(options)s\t%(maxcounts)s %(interval)s' % locals()
    append('/etc/fstab', line, use_sudo=True)

