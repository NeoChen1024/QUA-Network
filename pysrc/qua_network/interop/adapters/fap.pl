# SPDX-License-Identifier: Apache-2.0
#
# Adapter for the parser `fap` of docs/interop/09-comparison.md.
#
# The parser is the Perl module Ham::APRS::FAP of the submodule
# 3rdparty/perl-aprs-fap. This program runs as a process of its own. It
# calls the public function `parseaprs` of the module and copies no code
# of it.
#
# Usage: fap.pl LIBDIR
#
# Standard input has one packet per line, as the hexadecimal digits of the
# bytes of its TNC2 line. Standard output has one JSON object per packet:
# the hash that `parseaprs` fills, without `origpacket`, and `ok`, the
# return value of `parseaprs`.
use strict;
use warnings;
use JSON::PP;

my $dir = shift @ARGV;
require "$dir/FAP.pm";

# ascii: a byte above 0x7F is written as \u00XX, so that a text of the
# result gives the bytes of the packet back.
my $json = JSON::PP->new->ascii->canonical->allow_blessed->allow_unknown;
while (my $digits = <STDIN>) {
    chomp $digits;
    my $line = pack("H*", $digits);
    my %p;
    my $ok = eval { Ham::APRS::FAP::parseaprs($line, \%p) };
    if ($@) {
        %p = (resultcode => 'crash', resultmsg => "$@");
        $ok = 0;
    }
    delete $p{origpacket};
    $p{ok} = $ok ? 1 : 0;
    print $json->encode(\%p), "\n";
}
