#!/bin/sh
### BEGIN INIT INFO
# Provides:          garage
# Default-Start:     1 2 3 4 5
# Short-Description: Starts mitainesoft garage
# Description:       Starts mitainesoft garage
### END INIT INFO

PATH=/sbin:/usr/sbin:/bin:/usr/bin
. /lib/init/vars.sh

MITAINEGARAGEHOME=/opt/mitainesoft/garage
MITAINE_GARAGE_PROC=`ps -ef | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

do_start () {
	# Update motd
	#uname -snrvm > /var/run/motd.dynamic
	exec sudo -u mitainesoft /opt/mitainesoft/garage/watchdog_mitaine_garage.bash
}

do_status () {
	MITAINE_GARAGE_PROC=`ps -ef | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`
	if [ -n "$MITAINE_GARAGE_PROC" ]
	then
   		echo "garageURLCmdProcessor running PID='$MITAINE_GARAGE_PROC'"
	else
   		echo "launch_dashboard.bash not running($MITAINE_GARAGE_PROC)"
	fi

	/opt/vc/bin/vcgencmd measure_temp

}

case "$1" in
  start)
	do_start
	;;
  restart|reload|force-reload)
	echo "Error: argument '$1' not supported" >&2
	exit 3
	;;
  stop)
	# No-op
	echo "Process unstoppable !  You need to kill process and comment out crontab!"
	exit 4
	;;
  status)
	do_status
	exit $?
	;;
  *)
	echo "Usage: motd [start|stop|status]" >&2
	exit 3
	;;
esac

:
