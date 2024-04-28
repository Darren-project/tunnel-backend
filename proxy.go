package main

import (
	"flag"
	"io"
	"net"
	"time"

	log "github.com/sirupsen/logrus"
	"golang.org/x/net/proxy"
)

func pipe(src io.Reader, dst io.Writer) {
	_, err := io.Copy(dst, src)
	if err != nil {
		log.WithError(err).Warn("error copying data")
	}
}

func handleConnection(conn net.Conn, socks5, target string) {
	defer conn.Close()

	// Establish a SOCKS5 proxy connection
	dialer, err := proxy.SOCKS5("tcp", socks5, nil, &net.Dialer{
		Timeout:   60 * time.Second,
		KeepAlive: 30 * time.Second,
	})
	if err != nil {
		log.WithError(err).Warn("cannot initialize SOCKS5 proxy")
		return
	}

	// Dial the target server
	c, err := dialer.Dial("tcp", target)
	if err != nil {
		log.WithError(err).WithField("target", target).Warn("cannot dial target server")
		return
	}
	defer c.Close()

	// Set up data pipes
	up, down := make(chan struct{}), make(chan struct{})
	go func() {
		pipe(conn, c)
		close(up)
	}()
	go func() {
		pipe(c, conn)
		close(down)
	}()

	// Wait for data transfer to complete
	<-up
	<-down
}

func main() {
	local := flag.String("local", "127.0.0.1:9001", "address to listen")
	socks5 := flag.String("proxy", "127.0.0.1:1055", "SOCKS5 proxy")
	target := flag.String("target", "100.112.221.133:9001", "forwarding target")
	flag.Parse()

	lis, err := net.Listen("tcp", *local)
	if err != nil {
		log.WithError(err).Fatal("cannot listen")
	}

	for {
		conn, err := lis.Accept()
		if err != nil {
			log.WithError(err).Warn("cannot accept connection")
			continue
		}
		go handleConnection(conn, *socks5, *target)
	}
}

