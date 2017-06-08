import os
import StringIO
import random
from fabric.api import *
from fabric.operations import put, require
from fabric.contrib.files import exists, contains, append, first, sed
from awl_bfi_fabric.conf.settings import DATA_DIR

# source files
source = os.path.join(DATA_DIR, 'pci')
inst_clamav = 'install_clamav'
clamscan = 'clamscan'
clamwat = 'clamwat'

@task()
def del_signatures_pdf():
    ''' delete /usr/share/doc/clamavXXXX/signatures.pdf '''
    sudo('rm /usr/share/doc/clamav-0.97.1/signatures.pdf')

