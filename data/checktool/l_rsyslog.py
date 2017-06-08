#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Nagios plugin to test syslog
Written by Herve Vidalie the 03/07/2013
"""

__author__  = "Herve Vidalie"
__title__   = "Nagios plugin to test syslog"
__version__ = "0.4.2"

# Standard Nagios return codes
OK       = 0
WARNING  = 1
CRITICAL = 2
UNKNOWN  = 3

import os
import re
import sys
import signal
OLD_PYTHON = False
try:
    from subprocess import Popen, PIPE, STDOUT
except ImportError:
    OLD_PYTHON = True
    import commands
from optparse import OptionParser

DEFAULT_TIMEOUT = 60

if os.path.isfile("/etc/rsyslog.d/50_remote.conf"):
        RSYSLOG_CONF_DEFAULT_PATH = "/etc/rsyslog.d/50_remote.conf"
        REGEX = "^[^#].+target.+[0-9]+.+"
else:
        RSYSLOG_CONF_DEFAULT_PATH = "/etc/rsyslog.conf"
        REGEX = "^[^#].+@@.+:[0-9]+"

def end(status, message):
    """Exits the plugin with first arg as the return code and the second
    arg as the message to output"""

    check = "LOG "
    if status == OK:
        print "%sOK: %s" % (check, message)
        sys.exit(OK)
    elif status == WARNING:
        print "%sWARNING: %s" % (check, message)
        sys.exit(WARNING)
    elif status == CRITICAL:
        print "%sCRITICAL: %s" % (check, message)
        sys.exit(CRITICAL)
    else:
        print "UNKNOWN: %s" % message
        sys.exit(UNKNOWN)


class LogTester:
    """Class to hold all portage test functions and state"""

    def __init__(self):
        """Initialize all object variables"""

        self.hostname           = ""
        self.no_send_flag       = False
        self.destinations       = list()
        self.rsyslog_conf_path  = None
        self.timeout            = DEFAULT_TIMEOUT
        self.verbosity          = 0


    def validate_all_variables(self):
        """Validates all object variables to make sure the
        environment is sane"""

        if self.timeout == None:
            self.timeout = DEFAULT_TIMEOUT
        try:
            self.timeout = int(self.timeout)
        except ValueError:
            end(UNKNOWN, "Timeout must be a whole number, " \
                       + "representing the timeout in seconds")

        if self.timeout < 1 or self.timeout > 3600:
            end(UNKNOWN, "Timeout must be a number between 1 and 3600 seconds")

        if self.verbosity == None:
            self.verbosity = 0
        try:
            self.verbosity = int(self.verbosity)
            if self.verbosity < 0:
                raise ValueError
        except ValueError:
            end(UNKNOWN, "Invalid verbosity type, must be positive numeric " \
                        + "integer")

        if self.rsyslog_conf_path == None:
            self.rsyslog_conf_path = RSYSLOG_CONF_DEFAULT_PATH


    def run(self, cmd):
        """runs a system command and returns the output"""

        if cmd == "" or cmd == None:
            end(UNKNOWN, "Internal python error - " \
                       + "no cmd supplied for run function")

        self.vprint(3, "running command: %s" % cmd)

        if OLD_PYTHON:
            self.vprint(3, "subprocess not available, probably old python " \
                         + "version, using shell instead")
            returncode, stdout = commands.getstatusoutput(cmd)
            if returncode >= 256:
                returncode = returncode / 256
        else:
            try:
                process = Popen( cmd.split(),
                                 stdin=PIPE,
                                 stdout=PIPE,
                                 stderr=STDOUT )
            except OSError, error:
                error = str(error)
                if error == "No such file or directory":
                    end(UNKNOWN, "Cannot find utility '%s'" % cmd.split()[0])
                end(UNKNOWN, "Error trying to run utility '%s' - %s" \
                                                  % (cmd.split()[0], error))

            output = process.communicate()
            returncode = process.returncode
            stdout = output[0]

        self.vprint(3, "Returncode: '%s'\nOutput: '%s'" \
                                                     % (returncode, stdout))
        output = str(stdout)

        self.check_returncode(returncode, output)

        return output


    def check_returncode(self, returncode, output):
        """Takes the returncode and output (as an array of lines)
        of a command, exits with an appropriate message if any are found"""

        if returncode == 0:
            pass
        else:
            output = self.strip_output(output)
            end(UNKNOWN, "%s" % output)


    def set_timeout(self):
        """Sets an alarm to time out the test"""

        if self.timeout == 1:
            self.vprint(3, "setting plugin timeout to %s second" \
                                                                % self.timeout)
        else:
            self.vprint(3, "setting plugin timeout to %s seconds"\
                                                                % self.timeout)

        signal.signal(signal.SIGALRM, self.sighandler)
        signal.alarm(self.timeout)


    def sighandler(self, discarded, discarded2):
        """Function to be called by signal.alarm to kill the plugin"""

        end(CRITICAL, "Log nagios plugin has self terminated after " \
                    + "exceeding the timeout (%s seconds)" % self.timeout)


    def get_hostname(self):
        """Get the machine hostname and store it."""

        self.hostname = self.run("hostname").splitlines()[0]
        self.vprint(2, "Hostname: %s" % (self.hostname) )


    def check_rsyslog_conf_readable(self):
        """Checks that the rsyslog configuration file and path are correct
        and readable, otherwise exits with error"""

        if not os.path.exists(self.rsyslog_conf_path):
            end(UNKNOWN, "%s cannot be found" % self.rsyslog_conf_path)
        elif not os.path.isfile(self.rsyslog_conf_path):
            end(UNKNOWN, "%s is not a file" % self.rsyslog_conf_path)
        elif not os.access(self.rsyslog_conf_path, os.R_OK):
            end(UNKNOWN, "%s is not readable" % self.rsyslog_conf_path)

        self.vprint(2, "'%s' exists and is readable" % (self.rsyslog_conf_path) )


    def get_centrallog(self):
        """Reads the central logs hostnames and ports from the rsyslog.conf file"""

        self.check_rsyslog_conf_readable()

        try:
            file = open(self.rsyslog_conf_path, 'r')
        except IOError:
            file.close()
            end(WARNING, "Cannot open %s" % self.rsyslog_conf_path)
        else:
            text = file.read()
            self.vprint(3, self.rsyslog_conf_path + ':\n' + text)
            file.close()

        re_centrallog = re.compile(REGEX, re.MULTILINE)

        self.destinations = list()

        for line in re_centrallog.findall(text): # find the interesting lines in rsyslog.conf
            if os.path.isfile("/etc/rsyslog.d/50_remote.conf"):
                host=[z[8:-1] for z in line.split() if z.startswith('target')][0]
                port=[z[6:-1] for z in line.split() if z.startswith('port')][0]
                destination = str(host) + ":" + str(port)
            else:
                destination = line.split("@@")[1] # contains hostname:port
            try:
               ind = self.destinations.index(destination)
            except:
               self.destinations.append(destination)

        if len(self.destinations) == 0:
            end(WARNING, "No destination has been found")

        self.vprint(2, "Destinations are:")
        for destination in self.destinations:
            self.vprint(2, "%s" % destination)


    def check_connexion(self):
        """Checks that connections to central loggers are established"""

        output = self.run("netstat -tn")

        for destination in self.destinations:
            destination_name, destination_port = destination.split(":")
            output2 = self.run("host %s" % destination_name)
            ip = re.findall("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", output2)
            if len(ip)==0:
                end(CRITICAL, "Cannot determine ip of %s " % destination )
            re_destination = str(ip[0] + ":" + destination_port + " *ESTABLISHED")
            if not re.search(re_destination, output):
                end(CRITICAL, "Connection to %s is not established" \
                    % destination )
            else:
                self.vprint(2, "Connection to %s is established" \
                    % destination)

    def send_flag(self):
        """Sends a flag to each destination"""

        self.get_hostname()
        date = self.run("date --rfc-3339=seconds").splitlines()[0]

        flag = "%s # %s # ApertureScience" % (self.hostname, date)
        output = self.run("logger -p authpriv.info %s" % flag)
        self.vprint(1, "Flag sent: %s" % flag)

    def test_log(self):
        """Starts tests and controls logic flow
        Returns a tuple of the status code and output"""

        self.vprint(3, "%s - Version %s\nAuthor: %s\n" \
            % (__title__, __version__, __author__))

        self.validate_all_variables()
        self.set_timeout()

        self.get_centrallog()
        self.check_connexion()
        if not self.no_send_flag:
            self.send_flag()

        if len(self.destinations) == 1:
            return OK, "1 flag sent to %s" % self.destinations[0]
        else:
            message = str(len(self.destinations)) + " flags sent to "
            for destination in self.destinations:
                message += destination + " "
            return OK, message


    def vprint(self, threshold, message):
        """Prints a message if the first arg is numerically lower than the
        verbosity level"""

        if self.verbosity >= threshold:
            print "%s" % message


def main():
    """Parses command line options and calls the test function"""

    tester = LogTester()
    parser = OptionParser()

    parser.add_option( "-F",
                       "--no-send-flags",
                       action="store_true",
                       dest="no_send_flags",
                       help="Do not send flag to destinations. By default a " \
                          + "flag is sent to every destination. Format is: "  \
                          + "servername # date # ApertureScience")

    parser.add_option( "-p",
                       "--rsyslog_conf_path",
                       dest="rsyslog_conf_path",
                       help="Explicitly set the path to rsyslog.conf "
                          + "By default the path is /etc/rsyslog.conf")

    parser.add_option( "-t",
                       "--timeout",
                       dest="timeout",
                       help="Sets a timeout in seconds after which the "  \
                           +"plugin will exit (default is %s seconds). " \
                                                      % DEFAULT_TIMEOUT)

    parser.add_option( "-v",
                       "--verbose",
                       action="count",
                       dest="verbosity",
                       help="Verbose mode. Can be used multiple times to "     \
                          + "increase output. Use -vvv for debugging output. " \
                          + "By default only one result line is printed as "   \
                          + "per Nagios standards")

    parser.add_option( "-V",
                       "--version",
                       action="store_true",
                       dest="version",
                       help="Print version number and exit")

    (options, args) = parser.parse_args()

    if args:
        parser.print_help()
        sys.exit(UNKNOWN)

    tester.no_send_flags      = options.no_send_flags
    tester.timeout            = options.timeout
    tester.verbosity          = options.verbosity
    tester.rsyslog_conf_path  = options.rsyslog_conf_path

    if options.version:
        print "%s - Version %s\nAuthor: %s\n" \
            % (__title__, __version__, __author__)
        sys.exit(OK)

    result, output = tester.test_log()
    end(result, output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "Caught Control-C..."
        sys.exit(CRITICAL)

"""
=head1 NAME

l_rsyslog

=head1 OBJECTIVES AND NEEDS

Ce plugin a pour objectif de vérifier la connexion aux concentrateurs de log.

B<Auteur:> herve.vidalie@worldline.com

=head1 SYNOPSIS

./l_rsyslog [-F] [-p <path to rsyslog.conf>] [-t <timeout in second>]

=head1 CONTEXT

===Pré-requis===

Le langage utilisé est Python(2.7).

===Périmètre===

Le périmètre comprend les machines Linux.

=head1 OPTIONS

=over

=item B<-F, --no-send-flags>

Do not send flag to destinations. By default a flag is sent to every destination.

Format is: servername # date # ApertureScience

=item B<-p, --rsyslog_conf_path>

Explicitly set the path to rsyslog.conf By default the path is /etc/rsyslog.conf

=item B<-t,--timeout>

Sets a timeout in seconds after which the plugin will exit (defaults to 60 seconds).

=item B<-v,--verbose>

Verbose mode. Can be used multiple times to increase output. Use -vvv for debugging output. By default only one result line is printed as per Nagios standards.

=item B<-V,--version>

Print version number and exit.

=item B<-h,--help>

Print help.

=back

=head1 DESCRIPTION

Les informations sur le plugin sont les suivantes :

Nagios plugin to test syslog

Written by Herve Vidalie the 03/07/2013

===Principe===

-Vérification de l'existence du fichier rsyslog.conf

-Lecture de la configuration

-Vérication des connexions avec la commande netstat

-Envoi d'un flag à chaque concentrateur de log

Format du flag: servername # date # ApertureScience

=head1 TESTS TO REALIZE

Vérifie l'existence et l'accès en lecture du fichier /etc/rsyslog.conf

Retourne WARNING en cas d'erreur.

Lecture du fichier /etc/rsyslog.conf pour récupérer les hostnames et les ports des concentrateurs de logs.

Si aucun concentrateur de log n'est trouvé, retourne WARNING.

Exécution de la commande 'netstat -tn'

Vérification que toutes les connexions vers les concentrateurs de logs sont établies; sinon retourne CRITICAL.

Envoi d'un flag à chaque concentrateur de log contenant le terme 'ApertureScience'.

retourne OK.

=head1 FLOWCHART

=cut
"""
