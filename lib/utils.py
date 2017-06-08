from fabric.api import env, run, sudo, settings, hide, put

from fabric.contrib.files import upload_template as _upload_template

def run_as_root(command, *args, **kwargs):
    """
    Run a remote command as the root user.

    When connecting as root to the remote system, this will use Fabric's
    ``run`` function. In other cases, it will use ``sudo``.
    """
    if env.user == 'root':
        func = run
    else:
        func = sudo
    return func(command, *args, **kwargs)

 
def upload_template(*args, **kwargs):
    """
    Wrapper around ``fabric.contrib.files.upload_template`` to change ownership after upload
    http://docs.fabfile.org/en/1.8/api/contrib/files.html

    additionnal parameters:
      user  : 'root'
      group : 'root'
    """

    destination = args[1]
    user  = kwargs.pop('user', 'root')
    group = kwargs.pop('group', 'root')

    _upload_template(*args, **kwargs)
    with settings(hide('stdout')):
        run_as_root('chown %s:%s %s' % (user, group, destination))


def upload(*args, **kwargs):
    """
    Wrapper around ``fabric.operations.put`` to change ownership after upload
    http://docs.fabfile.org/en/1.8/api/core/operations.html#fabric.operations.put

    additionnal parameters :
      user  : 'root'
      group : 'root'
    """

    destination = args[1]
    user  = kwargs.pop('user', 'root')
    group = kwargs.pop('group', 'root')

    put(*args, **kwargs)
    with settings(hide('stdout')):
        run_as_root('chown %s:%s %s' % (user, group, destination))

