from pipes import quote
from fabric.api import hide, settings
from utils import run_as_root

def is_installed(rpm):
    """Check if an RPM package is installed."""

    with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        res = run_as_root('yum list installed %s' % quote(rpm))
        if res.succeeded:
            return True
        return False
