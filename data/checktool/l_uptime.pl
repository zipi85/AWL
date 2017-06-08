#!/usr/bin/perl -w
## $Id: l_uptime.pl,v 1.5 2012/10/18 14:29:15 a170885 Exp $
## plugin name - short description
#################################################################################
## Usage: l_uptime [-V|--version][-h|--help][-d|--debug]
##        l_uptime [-w|--min_warn][-W|--max_warn]
##        l_uptime [-c|--min_crit][-C|--max_crit]
## Author: nicolas.marlier@atos.net
## Date: 01/03/2012
#################################################################################
## Changelog:
## * 01/03/2012 : release initiale
## * 19 jul 2012 - benjamin.coudou@atos.net
## - add POD
## * 12 sept 2012 - benjamin.coudou@atos.net
## * JIRA TO-CHECKTOOLSV2-19
## * fix the return code.
## * 18 october 2012 - benjamin.coudou@atos.net
## - add author
#################################################################################
## DESCRIPTION :
## This plugin get the server uptime and compare it to
## * [-c|--min_crit] : minimum value -> if less : CRITICAL
## * [-C|--max_crit] : maximum value -> if more : CRITICAL
## * [-w|--min_warn] : minimum value -> if less : WARNING
## * [-W|--max_warn] : maximum value -> if more : WARNING
#################################################################################

use strict;
use Sys::Hostname;
use Getopt::Long;
use Carp;
use warnings;

########## common variables
my $PROGNAME = "l_uptime";
my ( $opt_V, $opt_h, $opt_T, $opt_w, $opt_W, $opt_c, $opt_C, $opt_d );

my $comment = q{};
our $VERSION = 1.1;
my %ERRORS = ( 'OK' => 0, 'WARNING' => 1, 'CRITICAL' => 2, 'UNKNOWN' => 3 );
my $debug = 0;

########## AWL CHECKTOOLV2 tag and function ##############
## RELEASE to choice after validation;
## stable,unstable, deprecated, local
my $RELEASE = "stable";

# Category to choice  according to goal of this plugin.
# system, security, network, database
my @CATEGORIES = ("system");

# OWNER according to the autor of this plugin
# FDS2_BFI, FDS2_TRP, ...
my $OWNER = "FDS2_BFI";

########## specific variables###############
my $uptime;
my ( $min_warn, $max_warn );
my ( $min_crit, $max_crit );


######### Option checking
Getopt::Long::Configure('bundling');
GetOptions(
    "V|version"  => \$opt_V,
    "h|help"     => \$opt_h,
    "T|tag"      => \$opt_T,
    "w=s"        => \$opt_w,
    "min_warn=s" => \$opt_w,
    "W=s"        => \$opt_W,
    "max_warn=s" => \$opt_W,
    "c=s"        => \$opt_c,
    "min_crit=s" => \$opt_c,
    "C=s"        => \$opt_C,
    "max_crit=s" => \$opt_C,
    "d|debug"    => \$opt_d
);

if ($opt_V) {
    print_version( $PROGNAME, $VERSION );
    exit $ERRORS{'OK'};
}
if ($opt_h) {
    print_help();
    exit $ERRORS{'OK'};
}
if ($opt_T) {
    print_tag();
    exit $ERRORS{'OK'};
}
if ($opt_d) {
    $debug = 1;
}
if ($opt_w) {
    $min_warn = $opt_w;
}
if ($opt_W) {
    $max_warn = $opt_W;
}
if ($opt_c) {
    $min_crit = $opt_c;
}
if ($opt_C) {
    $max_crit = $opt_C;
}
######### common functions
sub print_version {
    my $name = shift;
    my $rev  = shift;
    print "$name in version $rev. \n";
    return 1;
}

sub usage {
    print "plugins has to be describe [-V] [-h]  \n";
    print_help();
    return 1;
}

sub print_help {
    print "$PROGNAME ........";
    print "...................";
    print "\nUsage:\n";
    print "   -V (--version)    Plugin version\n";
    print "   -h (--help)       Usage help \n";
    print "   -T (--tag)        print AWL tags\n";
    print "   -d (--debug)      Debug Mode\n";
    print "   -c (--min_crit)   minimal value if less -> critical\n";
    print "   -C (--max_crit)   maximal value if more -> critical\n";
    print "   -w (--min_warn)   minimal value if less -> warning\n";
    print "   -W (--max_warn)   maximal value if more -> warning\n";
    print "\n";

    print_version( $PROGNAME, $VERSION );
    return 1;
}
# AWL functions for packaging
# # functions to classify plugins
# #see options -T
sub print_tag {
    print "release: ", $RELEASE, "\n";
    foreach (@CATEGORIES) {
        print "category: ", $_, "\n";
    }
    print "owner: ", $OWNER, "\n";
    return 1;
}

sub get_uptime {

    # Read the uptime in seconds from /proc/uptime, skip the idle time...
    open( my $FILE, "<", "/proc/uptime" ) or croak "Cannot open /proc/uptime";
    my ( $tmp_uptime, undef ) = split / /, <$FILE>;
    close $FILE;
    
    $uptime = int( $tmp_uptime /1440 /60 );
    
    return ($uptime);
    }
    
############### MAIN ########################
get_uptime;

if ($debug) { print "uptime : [$uptime]\n"; }
if ($debug) { print "min    : [$min_warn]|[$min_crit]\n"; }
if ($debug) { print "max    : [$max_warn]|[$max_crit]\n"; }

if ( $opt_c && $uptime < $min_crit ) {
    print "CRITICAL : uptime too short ($uptime < $min_crit)";
    exit $ERRORS{'CRITICAL'};
}

if ( $opt_C && $uptime > $max_crit ) {
    print "CRITICAL : uptime too long ($uptime > $max_crit)";
    exit $ERRORS{'CRITICAL'};
}

if ( $opt_w && $uptime < $min_warn ) {
    print
"WARNING : uptime too short ($uptime < $min_warn), server may have reboot recently";
    exit $ERRORS{'WARNING'};
}

if ( $opt_W && $uptime > $max_warn ) {
    print
"WARNING : uptime too long ($uptime > $max_warn), be carefull on next restart";
    exit $ERRORS{'WARNING'};
}

print "Uptime OK - $uptime jours";
exit $ERRORS{'OK'};

__END__

=head1 NAME

uptime

=head1 OBJECTIVES AND NEEDS

Ce plugin a pour objectif de vérifier la date du dernier reboot des serveurs Linux.

B<Auteur/Point de contact:> nicolas.thepot@atos.net

=head1 SYNOPSIS

./check_uptime [-c OPTION]|[-w OPTION] [-C OPTION]|[-W OPTION] [ -V ]

=head1 CONTEXT

===Pré-requis===

Le langage utilisé est le bash.



===Périmètre===

Le périmètre comprend les machines Linux (LFS, Red Hat)

=head1 OPTIONS

=over

=item B<-h,--help>

help

=item B<-c> minutes

CRITICAL MIN uptime

=item B<-w> minutes

WARNING  MIN uptime

=item B<-C> minutes

CRITICAL MAX uptime

=item B<-W> minutes

WARNING  MAX uptime

=item B<-V>

Version

=item B<>



=back

=head1 DESCRIPTION

Les informations sur le plugin sont les suivantes :



Auteur : Dmitry Vayntrub 03/11/2009



The plugin shows the uptime and optionally

compares it against MIN and MAX uptime thresholds

This script checks uptime and optionally verifies if the uptime

is below MINIMUM or above MAXIMUM uptime treshholds



=head1 TESTS TO REALIZE

n/a

=head1 FLOWCHART

=cut
           




                     


