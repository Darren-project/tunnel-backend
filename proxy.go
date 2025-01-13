package main

import (
	"flag"
	"io"
	"log"
	"net"
	"time"

	"golang.org/x/net/proxy"
)

// pipe copies data from src to dst and logs any errors encountered.
func pipe(src io.Reader, dst io.Writer, direction string) {
	_, err := io.Copy(dst, src)
	if err != nil {
		log.Printf("error in %s data transfer: %v", direction, err)
	}
}

// handleConnection manages the lifecycle of a single connection,
// forwarding data through the SOCKS5 proxy to the target server.
func handleConnection(conn net.Conn, socks5, target string) {
	defer conn.Close()

	// Create a SOCKS5 proxy dialer
	dialer, err := proxy.SOCKS5("tcp", socks5, nil, &net.Dialer{
		Timeout:   60 * time.Second,
		KeepAlive: 30 * time.Second,
	})
	if err != nil {
		log.Printf("cannot initialize SOCKS5 proxy: %v", err)
		return
	}

	// Dial the target server through the SOCKS5 proxy
	proxyConn, err := dialer.Dial("tcp", target)
	if err != nil {
		log.Printf("cannot dial target server %s: %v", target, err)
		return
	}
	defer proxyConn.Close()

	log.Printf("Forwarding connection to target %s via proxy %s", target, socks5)

	// Set up bidirectional data transfer
	errCh := make(chan error, 2)
	go func() {
		pipe(conn, proxyConn, "upstream")
		errCh <- nil
	}()
	go func() {
		pipe(proxyConn, conn, "downstream")
		errCh <- nil
	}()

	// Wait for either direction to complete
	select {
	case <-errCh:
		log.Printf("Connection to %s closed", target)
	}
}

func main() {
	// Define and parse command-line flags
	local := flag.String("local", "127.0.0.1:9001", "address to listen on")
	socks5 := flag.String("proxy", "127.0.0.1:1055", "SOCKS5 proxy address")
	target := flag.String("target", "100.112.221.133:9001", "forwarding target address")
	flag.Parse()

	// Start listening for incoming connections
	listener, err := net.Listen("tcp", *local)
	if err != nil {
		log.Fatalf("Failed to start listener on %s: %v", *local, err)
	}
	defer listener.Close()

	log.Printf("Listening on %s and forwarding to %s via proxy %s", *local, *target, *socks5)

	// Accept incoming connections in a loop
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		log.Printf("Accepted connection from %s", conn.RemoteAddr())
		go handleConnection(conn, *socks5, *target)
	}
}
