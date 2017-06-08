import os.path
import socket

from fabric.api import task, env

from awl_bfi_fabric.lib.utils import run_as_root, upload_template
from awl_bfi_fabric.conf.settings import TEMPLATE_DIR

from lib import filesystem


@task
def upload_hosts():
    """upload /etc/hosts with informations in the correct order"""
    
    # The informations in /etc/hosts when we deploy a VM deploying a VM
    # are not in the expect order. This generates troubles with the load-balancer 
    # in apache-tomcat-connector
    #
    # Change (@IP, fqdn, hostname) by (@IP, hostname, fqdn)
    file_host = '/etc/hosts'
    hostname = env.host
    
    # create dict to render the template
    d = dict(
        hostname = hostname,
        ip = socket.gethostbyname(hostname),
        fqdn = '.'.join([hostname, 'priv.atos.fr']),
        )

    template = os.path.join(TEMPLATE_DIR, 'system', 'etc_hosts')
    dest = '/etc/hosts'

    upload_template(template, dest, context=d, use_sudo=True, mode=0644)


