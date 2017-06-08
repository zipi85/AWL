import urllib

from fabric.api import env, task, hide, abort
from fabric.contrib.files import exists as file_exists, contains, append, sed

from awl_bfi_fabric.lib.utils import run_as_root
from awl_bfi_fabric.lib.system import get_distrib_name, get_distrib_version, get_arch


# list of activation key available
ACTIVATION_KEY = dict(
    ACK_MUTU_DEV_CENTOS_6_x86_64 = '26-6e44a6028dc165d1c22184e27a49486f',
    ACK_MUTU_DEV_RHEL_5_x86_64   = '26-3b44b8f22627712cd01a350aedc913a9',
    ACK_MUTU_DEV_RHEL_6_x86_64   = '26-aa45ee68c091b253adc27fc43dcc191f',
    ACK_MUTU_EAE_CENTOS_6_x86_64 = '26-32271a6c12f291374cff17441f04ea12',
    ACK_MUTU_EAE_RHEL_5_x86_64   = '26-95fa468355c73ad1078e1759c4689799',
    ACK_MUTU_EAE_RHEL_6_x86_64   = '26-cc16f7cda3197f59ca86607e1c7ef64e',
    ACK_MUTU_IAE_CENTOS_6_x86_64 = '26-3437005d2c428d97b8e8b45af8211bda',
    ACK_MUTU_IAE_RHEL_5_x86_64   = '26-3df6cf6410df4c85316b5929d4e282a1',
    ACK_MUTU_IAE_RHEL_6_x86_64   = '26-bde73ef88cb0bc4d5cec8e692e5cf38d',
    ACK_MUTU_PRD_CENTOS_6_x86_64 = '26-c949a24033181113be9190892bd5b4fa',
    ACK_MUTU_PRD_RHEL_5_x86_64   = '26-18953ba962f3212a40bb02c29c71d19a',
    ACK_MUTU_PRD_RHEL_6_x86_64   = '26-8d16070a1e030e196e420c2f57ec86ad',
    ACK_PCI_PRD_CENTOS_6_x86_64  = '21-285ea5711b88f48e42a9f098e412a4e0',
    ACK_PCI_PRD_RHEL_5_x86_64    = '21-c3fc0f0183c2d8c5f4a651b73e73fcec',
    ACK_PCI_PRD_RHEL_6_x86_64    = '21-a985c6407fffc3e3c511e5d5c6aa0425',
    )

# Accepted organizations
ORGANIZATION = ('MUTU', 'PCI')

# Location of AWL Datacenter
# The letter representing the location in the hostname is the last one
# wiki : https://wiki/wiki/index.php/Naming

# BUG : spacewalk proxy of Vendome is not available 
# workaround: using the proxy of Seclin 
# SITE = ('Vendome', 'Seclin', 'Frankfurt', 'Brussels')
SITE = ('Seclin', 'Seclin', 'Frankfurt', 'Brussels')
LOCATION_LETTER = ('v', 's', 'k', 'b')
LOCATION_LETTER_TO_SITE = dict(zip(LOCATION_LETTER, SITE))

# The letter representing the environment in the hostname is the 2nd letter
ENV_LETTER = ('d', 'q', 's', 'p')
ENV_SPACEWALK = ('DEV', 'IAE', 'EAE', 'PRD')
ENV_COMMON = ('DEV', 'RCI', 'RCE', 'PRD')
ENV_LETTER_TO_ENV_SPACEWALK = dict(zip(ENV_LETTER, ENV_SPACEWALK))
ENV_COMMON_TO_ENV_SPACEWALK = dict(zip(ENV_COMMON, ENV_SPACEWALK))



def is_registered():
    """Check if host is registered."""
    spacewalk_url = "http://spacewalk-mutualized-fr-01.priv.atos.fr:8001/system/%s" % env.host
    response = urllib.urlopen(spacewalk_url, proxies=urllib.getproxies())
    content = response.read()
    if content == "[]":
        return False
    else:
        return True


def awl_script_is_installed():
    """Check if /usr/sbin/awl_sw_register_client_base.sh is installed."""
    return file_exists('/usr/sbin/awl_sw_register_client_base.sh')


def get_activation_key(organization, environment):
    """Return the activation key to use to register the server."""

    # retrieve information about the host
    distrib = get_distrib_name().upper()
    version = get_distrib_version().split('.')[0]
    arch = get_arch()
    description = '_'.join(['ACK', organization, environment, distrib, version, arch])

    try:
        return ACTIVATION_KEY[description]
    except KeyError:
        abort("Activation key not available.")


@task()
def register(organization, environment="", site=""):
    """register a server on spacewalk 
    
    Usage : fab spacewalk.register:organization[,environment=environment,site=site] -H host1,hostn

    :param organization: organization to register the server (mandatory)
                         available organization are :
                         - MUTU which stand for ORG-FR-DS_BFI-MUTU
                         - PCI  which stand for ORG-FR-DS_BFI-PCI
    
    :param environment: type of environment
                        available environment  : DEV, RCI, RCE or PRD (optional)
    
    :param site: location of the spacewalk proxy to use (optional)
                 available site: Vendome, Seclin, Frankfurt, Brussels 

                 
    Examples:    
    fab spacewalk.register:PCI -H tppci001v  
    fab spacewalk.register:MUTU,environment=RCE -H tsxxx001v
    fab spacewalk.register:MUTU,environment=DEV,site=Seclin -H tdxxx001s

    """

    if organization not in ORGANIZATION:
        abort("Organization %(organization)s is not supported")

    if not environment:
        # try to determine the environment from the hostname
        # define by the 2nd letter
        second_letter = env.host[1].lower()
        try:
            environment = ENV_LETTER_TO_ENV_SPACEWALK[second_letter]
        except KeyError:
            abort("Could not determine the environment")
    elif environment.upper() in ENV_COMMON:
        environment = ENV_COMMON_TO_ENV_SPACEWALK[environment.upper()]
    elif environment not in ENV_SPACEWALK:
        abort("Environment %s is not supported" % environment)

    if not site:
        # try to determine the site from the hostname 
        # define by the last letter
        last_letter = env.host[-1].lower()
        try :
            site = LOCATION_LETTER_TO_SITE[last_letter]
        except KeyError:
            abort("Could not determine the site")
    elif site not in SITE:
        abort("Unknown site %s" % site)


    if not is_registered():
        if awl_script_is_installed():
            activation_key = get_activation_key(organization, environment)
            with hide('stdout'):
                run_as_root('/usr/sbin/awl_sw_register_client_base.sh -a %s -s %s' % (activation_key, site))
        else:
            abort('rpm awl-spacewalk_scripts-base is not installed')
    else:
        print "server is already registered"

@task()
def exclude_in_yum(rpm=None):
    ''' add exclusion list in /etc/yum.conf '''
    if not rpm:
    	abort("Expected argument rpm")
    if contains('/etc/yum.conf','^exclude',exact=True,use_sudo=True,escape=False):
        print 'env.host', ' exclude already exists in /etc/yum.conf, updating '
        sed('/etc/yum.conf', before='^exclude.*$', after='&'+' '+rpm, limit='', use_sudo=True, backup='.bak', flags='', shell=False)
    else:
        print env.host, ' inserting exclude in /etc/yum.conf '
        append('/etc/yum.conf', 'exclude='+rpm, use_sudo=True, partial=False, escape=True, shell=False)

