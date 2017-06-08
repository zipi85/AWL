from fabric.api import *
from fabric.contrib import *
from fabric.contrib.files import *
import crypt, getpass
from datetime import datetime

@task
def change():
    """
    change passwd
    """
    pwd = env.host[-3:-1]
    if env.host[1] == 'p':
        pwd = 'tul(p'+pwd[::-1]
    else:
        pwd = 'l(las'+pwd[::-1]

    salt="$6$"+datetime.today().strftime('%d%a%f%b%S')[0:16]+"$"
    passwd = crypt.crypt(pwd,salt)
    sudo(("echo 'root:%s'|chpasswd -e")%(passwd))
