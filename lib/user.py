from pipes import quote

from fabric.api import hide, run, settings, sudo, local

from group import (
    exists as _group_exists,
    create as _group_create,
)

from utils import run_as_root


def exists(name):
    """
    Check if a user exists.
    """
    with settings(hide('running', 'stdout', 'warnings'), warn_only=True):
        return run('getent passwd %(name)s' % locals()).succeeded


def create(name, comment=None, home=None, create_home=None, skeleton_dir=None,
           group=None, create_group=True, extra_groups=None, password=None,
           system=False, shell=None, uid=None, non_unique=False):
    """
    Create a new user and its home directory.

    If *create_home* is ``None`` (the default), a home directory will be
    created for normal users, but not for system users.
    You can override the default behaviour by setting *create_home* to
    ``True`` or ``False``.

    If *system* is ``True``, the user will be a system account. Its UID
    will be chosen in a specific range, and it will not have a home
    directory, unless you explicitely set *create_home* to ``True``.

    If *shell* is ``None``, the user's login shell will be the system's
    default login shell (usually ``/bin/bash``).

    If *password* is ``True``, the password will be set to 0 (to allow SSH connection)
    """

    # Note that we use useradd (and not adduser), as it is the most
    # portable command to create users across various distributions:
    # http://refspecs.linuxbase.org/LSB_4.1.0/LSB-Core-generic/LSB-Core-generic/useradd.html

    args = []
    if comment:
        args.append('-c %s' % quote(comment))
    if home:
        args.append('-d %s' % quote(home))
    if group:
        args.append('-g %s' % quote(group))
        if create_group:
            if not _group_exists(group):
                _group_create(group)
    if extra_groups:
        groups = ','.join(quote(group) for group in extra_groups)
        args.append('-G %s' % groups)

    if create_home is None:
        create_home = not system
    if create_home is True:
        args.append('-m')
    elif create_home is False:
        args.append('-M')

    if skeleton_dir:
        args.append('-k %s' % quote(skeleton_dir))
    if password:
        args.append('-p 0')
    if system:
        args.append('-r')
    if shell:
        args.append('-s %s' % quote(shell))
    if uid:
        args.append('-u %s' % quote(uid))
        if non_unique:
            args.append('-o')
    args.append(name)
    args = ' '.join(args)
    run_as_root('useradd %s' % args)


def modify(name, comment=None, home=None, move_current_home=False, group=None,
           extra_groups=None, login_name=None, password=None, shell=None,
           uid=None, non_unique=False):
    """
    Modify an existing user.
    """

    args = []
    if comment:
        args.append('-c %s' % quote(comment))
    if home:
        args.append('-d %s' % quote(home))
        if move_current_home:
            args.append('-m')
    if group:
        args.append('-g %s' % quote(group))
    if extra_groups:
        groups = ','.join(quote(group) for group in extra_groups)
        args.append('-G %s' % groups)
    if login_name:
        args.append('-l %s' % quote(login_name))
    if password:
        args.append('-p 0')
    if shell:
        args.append('-s %s' % quote(shell))
    if uid:
        args.append('-u %s' % quote(uid))
        if non_unique:
            args.append('-o')

    if args:
        args.append(name)
        args = ' '.join(args)
        run_as_root('usermod %s' % args)


def unlock(name):
    """
    Unlock an existing user, set password to 0.
    """
    modify(name, password=True)


def delete(name):
    """
    Delete an existing user.
    """
    if exists(name):
        run_as_root('userdel %s' % quote(name))

