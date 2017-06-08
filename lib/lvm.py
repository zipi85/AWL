from fabric.api import hide, settings, abort

from utils import run_as_root


def vg_exists(vgname):
    """
    Check if volum group exists.
    """
    with settings(hide('running', 'stdout', 'warnings'), warn_only=True):
        return run_as_root('vgs %(vgname)s' % locals()).succeeded


def lv_exists(lvname, vgname):
    """
    Check if logical volum exists.
    """
    with settings(hide('running', 'stdout', 'warnings'), warn_only=True):
        res = run_as_root('lvs --noheadings -o lv_name %(vgname)s' % locals())
        return lvname in res.split()


def lvcreate(lvname, size, vgname):
    """
    Create a logical volum.
    """
    if not vg_exists(vgname):
        abort('VG %(vgname)s does not exist.' % locals())

    if not lv_exists(lvname, vgname):
        with settings(hide('stdout', 'warnings'), warn_only=True):
            run_as_root('lvcreate -L %(size)s -n %(lvname)s %(vgname)s' % locals())
    else:
        abort('LV %(lvname)s already exists.' % locals())

