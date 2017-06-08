import os.path

from fabric.api import *

from awl_bfi_fabric.lib.utils import run_as_root, upload
from awl_bfi_fabric.lib.system import get_distrib_version
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR


@task()
def add_cron_clean_all():
    """
    upload crontab to clean up /var/cache/yum/

    Usage: fab repos.add_cron_clean_all -H host1,hostn
    """

    src = os.path.join(TEMPLATE_DIR, 'repos', 'yum-clean-all.cron')
    dst = '/etc/cron.d/yum-clean-all'
    upload(src, dst, use_sudo=True, mode=0600)


@task()
def add_disable_repos():
    """
    upload crontab and shell to disable the repos

    Usage: fab repos.add_disable_repos -H host1,hostn
    """

    # cron file
    src_cron = os.path.join(TEMPLATE_DIR, 'repos', 'disable-repos.cron')
    dst_cron = '/etc/cron.d/disable-repos'

    # shell 
    src_shell = os.path.join(TEMPLATE_DIR, 'repos', 'disable-repos')
    dst_shell = '/usr/local/bin/disable-repos'

    # upload cron
    upload(src_cron, dst_cron, use_sudo=True, mode=0600)

   # upload shell
    upload(src_shell, dst_shell, use_sudo=True, mode=0700)


@task()
def add_yum_post_action():
    """
    upload yum post-actions script to delete official centos repos

    Usage: fab repos.add_yum_post_action -H host1,hostn
    """

    # post-actions is available only on C6+
    if get_distrib_version().startswith('6'):
	with settings(hide('stdout')):
            run_as_root('yum -y install yum-plugin-post-transaction-actions.noarch')

        src = os.path.join(TEMPLATE_DIR, 'repos', 'remove-centos-repos.action')
        dst = '/etc/yum/post-actions/remove-centos-repos.action'
        upload(src, dst, use_sudo=True, mode=0644)


@task()
def deploy_all():
    """
    launch all the functions available in the module repos

    same as 
        fab repos.add_cron_clean_all -H host1,hostn
        fab repos.add_disable_repos -H host1,hostn
        fab repos.add_yum_post_action -H host1,hostn

    Usage: fab repos.deploy_all -H host1,hostn
    """
    add_cron_clean_all()
    add_disable_repos()
    add_yum_post_action()
