package main

import (
	"RDTReceiver/rdt_receiver"
	"flag"
	"net"
	"os"
)

type RDTReceiver struct {
	remoteAddr    *net.UDPAddr
	localAddr     *net.UDPAddr
	fileToReceive *os.File
}

func main() {
	// Parse the args
	remoteIP := flag.String("backward_recv_address", "127.0.0.1", "host address of the network emulator")
	remotePort := flag.Int("backward_recv_port", 23241, "DP port number used by the link emulator to receive ACKs from the receiver")
	localPort := flag.Int("receiver_recv_port", 37898, "UDP port number used by the receiver to receive data from the emulator")
	filename := flag.String("file", "fileReceived.txt", "name of the file into which the received data is written")

	flag.Parse()

	builder := rdt_receiver.Builder{}
	receiver := builder.
		SetRemoteAddress(*remoteIP, *remotePort).
		SetLocalAddress("", *localPort). // listen to all local IPs
		SetFileReceived(*filename).
		GetReceiver()

	receiver.Start()

}
