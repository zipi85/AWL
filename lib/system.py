import re
from fabric.api import *

# LSB format: "distro release x.x (codename)"
_lsb_release_version = re.compile(r'(.+)'
                                   ' release '
                                   '([\d.]+)'
                                   '[^(]*(?:\((.+)\))?')


def _get_release_infos():
    """Return a tuple containing distrib, release and codename"""
    
    # support RHEL or CentOS, we don't care about the rest...
    with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
        infos = run('cat /etc/redhat-release')
    
    m = _lsb_release_version.match(infos)
    if m is not None:
        return tuple(m.groups())
    else:
        abort('OS not supported.')


def get_distrib_name():
    """Return the distrib name."""
    distrib, version, codename = _get_release_infos()
    
    if distrib.startswith('Red Hat Enterprise Linux'):
        return 'RHEL'
    elif distrib.startswith('CentOS'):
        return 'CentOS'
    else:
        abort("OS not supported.")


def get_distrib_version():
    """Return the distrib version."""
    distrib, version, codename = _get_release_infos()    
    return version


def get_arch():
    """Return the CPU architecture."""
    with settings(hide('running', 'stdout')):
        arch = run('uname -m')
        return arch
