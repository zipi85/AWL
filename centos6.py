from fabric.api import *
from fabric.operations import put, require
from fabric.contrib.files import exists, contains, append, first, sed, comment
import urllib, re
import dataset
from io import StringIO

@task()
def find_vid():
        """find all ifcfg- containing VID=*"""
        x=sudo("grep -ilE '^vid=' /etc/sysconfig/network-scripts/ifcfg-*",warn_only=True)
        if x.succeeded:
                y=";".join(x.splitlines())
                print (("To correct : %s ==> %s")%(env.host,y))
@task()
def suppress_vid():
        """remove VID= from ifcfg-"""
        x=sudo("grep -ilE '^vid=' /etc/sysconfig/network-scripts/ifcfg-*",warn_only=True)
        if x.succeeded:
            for y in x.splitlines():
                comment(y,r'^VID=',use_sudo=True,backup='')
