import re
import sys
import urllib
from fabric.api import *
from fabric.operations import put, require
from fabric.contrib.files import contains, append, sed, exists

@task()
def disable_monitor():
    """add directive `disable monitor' to correct CVE-2013-5211"""
    append('/etc/ntp.conf', 'disable monitor', use_sudo=True)
    sudo('service ntpd restart')

@task()
def xen_independent_wallclock():
    """add directive `xen.independent_wallclock = 1' to /etc/sysctl.conf"""
    # apply this only on xen 
    if exists('/proc/xen/capabilities'):
        # force a check because the directive might be setup w/o a space between the equal sign 
        if not contains('/etc/sysctl.conf', 'xen.independent_wallclock', use_sudo=True):
            append('/etc/sysctl.conf', 'xen.independent_wallclock = 1', use_sudo=True)
            sudo('sysctl -p')
