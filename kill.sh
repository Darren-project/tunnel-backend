ps axf | grep "./socat" | grep -v grep | awk '{print "kill -15 " $1}' | sh
