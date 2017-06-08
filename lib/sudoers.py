import os.path

from fabric.api import *
from fabric.contrib.files import upload_template 

from utils import run_as_root
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR


def app(user):
    """
    Generate and delivers the sudoers file for an app user.
    """

    # setup variables
    d = dict(app=user.lower(), APP=user.upper())
    dest = os.path.join('/etc/sudoers.d', user)
    template = os.path.join(TEMPLATE_DIR, 'sudoers', 'app.sudoers')

    # load template and substitute variables
    upload_template(template, dest, context=d, use_sudo=True, mode=0440)
    with settings(hide('stdout')):
        sudo('chown root:root %s' % dest)


def upload_sudo_lcmd():
    """
    Delivers /usr/local/bin/sudo_lcmd
    """
    src = os.path.join(TEMPLATE_DIR, 'sudoers', 'sudo_lcmd')
    dest = '/usr/local/bin/sudo_lcmd'
    
    put(src, dest, use_sudo=True, mode=0755)
    with settings(hide('stdout')):
        run_as_root('chown root:root %s' % dest)

