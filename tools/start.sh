#!/bin/bash

function init {
	return 0
}

function start_process {
	sudo nohup python3 ./app.py >/dev/null 2>&1 &
	return 0
}
function stop_process {
        ps -ax|grep 'python'|grep 'flask'|awk '{print $1}'| xargs sudo kill -9
        sleep 1
	return 0
}

function main {
   RETVAL=0
   
   case "$1" in
      start)                                               # starts the Java program as a Linux service
		init
		start_process	
         ;;
      stop)                                                # stops the Java program service
        stop_process
         ;;
      restart)                                             # stops and restarts the service
         stop_process && start_process
         ;;
      *)
         echo "Usage: $0 {start|stop|restart}"
         exit 1
         ;;
      esac
   exit $RETVAL
}

 
main $1
