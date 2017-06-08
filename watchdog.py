import os.path

from fabric.api import *

from awl_bfi_fabric.lib.utils import run_as_root, upload
from awl_bfi_fabric.lib.system import get_distrib_version
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR


@task()
def add_menu_watchdog():
    """upload menu watchdog for integ"""

    # only available on C6+
    if get_distrib_version().startswith('6'):
        src_sudo = os.path.join(TEMPLATE_DIR, 'watchdog', 'menu-watchdog.sudoers')
        dst_sudo = '/etc/sudoers.d/menu-watchdog'
        upload(src_sudo, dst_sudo, use_sudo=True, mode=0440)

        src_menu = os.path.join(TEMPLATE_DIR, 'watchdog', 'menu-watchdog.c6')
        dst_menu = '/opt/local/watch_script/Watchdog_LWDA_menu.ksh'
	run_as_root('mkdir -p /opt/local/watch_script && chmod 755 /opt/local/watch_script')
        upload(src_menu, dst_menu, use_sudo=True, mode=0755)
    else:
        abort('OS not supported')

