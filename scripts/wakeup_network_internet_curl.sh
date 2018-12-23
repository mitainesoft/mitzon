#!/bin/sh
### BEGIN INIT INFO
# makes a call to a web site to ensure that routing is OK.
# Work around for weird behavior of local internet
# Call from cron
# 28 5,9,16,19 * * * /opt/mitainesoft/mitzon/scripts/wakeup_network_internet_curl.sh
### END INIT INFO
#

#Force a query to internet. To wake up timer. Kill previous curl !
echo Do a https request toward internet to wake up networks...
kill -9 `pgrep -f "curl -s -o /tmp/mitzon_curl.out http://jquery.com"` 2>/dev/null
nohup curl  -s -o /tmp/mitzon_curl.out https://code.jquery.com &

