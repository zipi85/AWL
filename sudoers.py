import os.path

from fabric.api import task
from fabric.contrib.files import exists, contains, append

from awl_bfi_fabric.lib.utils import run_as_root, upload, upload_template
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR

def _find_sudo_app():
    apps=run_as_root('ls -1 /etc/sudoers.d/???|xargs -Iapp basename app')
    return apps

@task
def app(user,source=None):
    """generate and delivers the sudoers file for an app user"""

    # setup variables
    d = dict(app=user.lower(), APP=user.upper())
    dest = os.path.join('/etc/sudoers.d', user)
    if source is None:
        template = os.path.join(TEMPLATE_DIR, 'sudoers', 'app.sudoers')
    else:
        template = os.path.join(TEMPLATE_DIR, 'sudoers', source+'.app.sudoers')

    # load template and substitute variables
    upload_template(template, dest, context=d, use_sudo=True, mode=0440)


@task
def upload_sudo_lcmd():
    """upload /usr/local/bin/sudo_lcmd"""
    src = os.path.join(TEMPLATE_DIR, 'sudoers', 'sudo_lcmd')
    dest = '/usr/local/bin/sudo_lcmd'

    upload(src, dest, use_sudo=True, mode=0755)

@task
def find_sudo_app():
    """ find all applications for which a separate member exists in /etc/sudoers.d """
    apps=_find_sudo_app()
    for x in apps.splitlines():
      print 'app found',x

@task
def secure_sudo_less():
    """ define env file for sudo so lesssecure is set """
    dest='/etc/sudo_env'
    template = os.path.join(TEMPLATE_DIR, 'sudoers', 'sudo_env')
    upload_template(template, dest, use_sudo=True, mode=0440)
    append('/etc/sudoers','Defaults    env_file =/etc/sudo_env',use_sudo=True)

@task
def reapply_apps(source=None):
    """ reset the sudoers file for all app user """
    apps=_find_sudo_app()
    for x in apps.splitlines():
        print 'reapplying sudoers for ',x
        app(x,source)
