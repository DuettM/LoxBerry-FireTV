#!/usr/bin/perl
use strict;
use warnings;
use LoxBerry::System;
use LoxBerry::Web;

# If index.cgi is accidentally opened inside the plugin iframe, redirect to
# the real FireTV dashboard to avoid recursively nesting the LoxBerry shell.
if (($ENV{HTTP_SEC_FETCH_DEST} // '') eq 'iframe') {
    print "Status: 302 Found\r\nLocation: dashboard.cgi\r\nCache-Control: no-store\r\n\r\n";
    exit 0;
}

LoxBerry::Web::lbheader('Fire TV Control','https://www.loxberry.de','', 'nojqm');
print <<'HTML';
<style>
.firetv-shell{width:100%;height:calc(100vh - 150px);min-height:720px;border:0;display:block;background:#f6f8f9}
@media(max-width:800px){.firetv-shell{height:calc(100vh - 115px);min-height:650px}}
</style>
<iframe class="firetv-shell" src="dashboard.cgi" title="Fire TV Control"></iframe>
HTML
LoxBerry::Web::lbfooter();
