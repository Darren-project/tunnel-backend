ps axf | grep "go run proxy.go" | grep -v grep | awk '{print "kill -15 " $1}' | sh
ps axf | grep "/exe/proxy" | grep -v grep | awk '{print "kill -15 " $1}'
