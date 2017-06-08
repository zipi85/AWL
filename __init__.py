import sys
from fabric.api import task, env

import appenv
import sudoers
import system
import repos
import patch
import patchquaterly
import patchmonthly
import watchdog
import acacia
import tripwire
import spacewalk
import checktool
import vmware
import ntp
import sssd
import itdiscovery
import pvm
import centos6
import pci
import passwd
import tsm

@task()
def load(filename):
    """load hosts from a file"""
    env.hosts = []

    try:
        with open(filename) as f:
            for line in f.readlines():
                # remove comment
                if line.strip().startswith('#'):
                    continue
                # not empty
                if line.strip():
                    env.hosts.append(line.strip())
    except IOError as e:
        print "%s : %s" % (filename, e.strerror)
        sys.exit(1)
