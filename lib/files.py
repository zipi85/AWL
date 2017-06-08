from pipes import quote
import os

from fabric.api import abort, hide, run, settings, sudo, warn
from fabric.contrib.files import upload_template as _upload_template
from fabric.contrib.files import exists

from utils import run_as_root


def is_file(path, use_sudo=False):
    """
    Check if a path exists, and is a file.
    """
    func = use_sudo and run_as_root or run
    with settings(hide('running', 'warnings'), warn_only=True):
        return func('[ -f "%(path)s" ]' % locals()).succeeded


def is_dir(path, use_sudo=False):
    """
    Check if a path exists, and is a directory.
    """
    func = use_sudo and run_as_root or run
    with settings(hide('running', 'warnings'), warn_only=True):
        return func('[ -d "%(path)s" ]' % locals()).succeeded


def is_link(path, use_sudo=False):
    """
    Check if a path exists, and is a symbolic link.
    """
    func = use_sudo and run_as_root or run
    with settings(hide('running', 'warnings'), warn_only=True):
        return func('[ -L "%(path)s" ]' % locals()).succeeded


def owner(path, use_sudo=False):
    """
    Get the owner name of a file or directory.
    """
    func = use_sudo and run_as_root or run
    # I'd prefer to use quiet=True, but that's not supported with older
    # versions of Fabric.
    with settings(hide('running', 'stdout'), warn_only=True):
        result = func('stat -c %%U "%(path)s"' % locals())
        if result.failed and 'stat: illegal option' in result:
            # Try the BSD version of stat
            return func('stat -f %%Su "%(path)s"' % locals())
        else:
            return result


def group(path, use_sudo=False):
    """
    Get the group name of a file or directory.
    """
    func = use_sudo and run_as_root or run
    # I'd prefer to use quiet=True, but that's not supported with older
    # versions of Fabric.
    with settings(hide('running', 'stdout'), warn_only=True):
        result = func('stat -c %%G "%(path)s"' % locals())
        if result.failed and 'stat: illegal option' in result:
            # Try the BSD version of stat
            return func('stat -f %%Sg "%(path)s"' % locals())
        else:
            return result


def mode(path, use_sudo=False):
    """
    Get the mode (permissions) of a file or directory.

    Returns a string such as ``'0755'``, representing permissions as
    an octal number.
    """
    func = use_sudo and run_as_root or run
    # I'd prefer to use quiet=True, but that's not supported with older
    # versions of Fabric.
    with settings(hide('running', 'stdout'), warn_only=True):
        result = func('stat -c %%a "%(path)s"' % locals())
        if result.failed and 'stat: illegal option' in result:
            # Try the BSD version of stat
            return func('stat -f %%Op "%(path)s"|cut -c 4-6' % locals())
        else:
            return result


def md5sum(filename, use_sudo=False):
    """
    Compute the MD5 sum of a file.
    """
    func = use_sudo and run_as_root or run
    with settings(hide('running', 'stdout', 'stderr', 'warnings'),
                  warn_only=True):
        # Linux (LSB)
        if exists(u'/usr/bin/md5sum'):
            res = func(u'/usr/bin/md5sum %(filename)s' % locals())
        # BSD / OS X
        elif exists(u'/sbin/md5'):
            res = func(u'/sbin/md5 -r %(filename)s' % locals())
        # SmartOS Joyent build
        elif exists(u'/opt/local/gnu/bin/md5sum'):
            res = func(u'/opt/local/gnu/bin/md5sum %(filename)s' % locals())
        # SmartOS Joyent build
        # (the former doesn't exist, at least on joyent_20130222T000747Z)
        elif exists(u'/opt/local/bin/md5sum'):
            res = func(u'/opt/local/bin/md5sum %(filename)s' % locals())
        # Try to find ``md5sum`` or ``md5`` on ``$PATH`` or abort
        else:
            md5sum = func(u'which md5sum')
            md5 = func(u'which md5')
            if exists(md5sum):
                res = func('%(md5sum)s %(filename)s' % locals())
            elif exists(md5):
                res = func('%(md5)s %(filename)s' % locals())
            else:
                abort('No MD5 utility was found on this system.')

    if res.succeeded:
        parts = res.split()
        _md5sum = len(parts) > 0 and parts[0] or None
    else:
        warn(res)
        _md5sum = None

    return _md5sum


def uncommented_lines(filename, use_sudo=False):
    """
    Get the lines of a remote file, ignoring empty or commented ones
    """
    func = run_as_root if use_sudo else run
    res = func('cat %s' % quote(filename), quiet=True)
    if res.succeeded:
        return [line for line in res.splitlines()
                if line and not line.startswith('#')]
    else:
        return []
