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
# the hash that `parseaprs` fills, and `ok`, the return value of
# `parseaprs`. The members `origpacket`, `body` and `header` repeat the
# input, and the adapter leaves them out.
#
# The adapter writes each scalar as text: a Perl scalar has no fixed type.
# It writes the JSON itself. The encoder JSON::PP of the Perl core took
# most of the run time.
use strict;
use warnings;

my $dir = shift @ARGV;
require "$dir/FAP.pm";

# A byte outside 0x20-0x7E is written as \u00XX, so that a text of the
# result gives the bytes of the packet back.
sub str {
    my $s = shift;
    if ($s =~ /[^\x20\x21\x23-\x5b\x5d-\x7e]/) {
        $s =~ s/(["\\])/\\$1/g;
        $s =~ s/([^\x20-\x7e])/sprintf('\\u%04x', ord($1))/ge;
    }
    return "\"$s\"";
}

sub enc {
    my $v = shift;
    my $r = ref $v;
    return defined $v ? str($v) : 'null' if !$r;
    return '{' . join(',', map { str($_) . ':' . enc($v->{$_}) } sort keys %$v) . '}' if $r eq 'HASH';
    return '[' . join(',', map { enc($_) } @$v) . ']' if $r eq 'ARRAY';
    return 'null';
}

while (my $digits = <STDIN>) {
    chomp $digits;
    my $line = pack("H*", $digits);
    my %p;
    my $ok = eval { Ham::APRS::FAP::parseaprs($line, \%p) };
    if ($@) {
        %p = (resultcode => 'crash', resultmsg => "$@");
        $ok = 0;
    }
    delete @p{qw(origpacket body header)};
    $p{ok} = $ok ? 1 : 0;
    print enc(\%p), "\n";
}
