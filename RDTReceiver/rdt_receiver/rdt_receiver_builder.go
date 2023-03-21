package rdt_receiver

import (
	"log"
	"net"
	"os"
	"sync"
)

type BuildProcess interface {
	SetRemoteAddress(remoteIP string, remotePort int) BuildProcess
	SetLocalAddress(localIP string, localPort int) BuildProcess
	SetFileReceived(filename string) BuildProcess
	setUdpSocket() BuildProcess
	setUpLogger() BuildProcess
	setMisc() BuildProcess
	GetReceiver() RDTReceiver
}

type Builder struct {
	receiver RDTReceiver
}

func (b *Builder) setMisc() BuildProcess {
	b.receiver.globalQuit = make(chan interface{})
	b.receiver.waitGroup = &sync.WaitGroup{}
	b.receiver.receiveBase = SeqNum(0) // expected for the first packet
	b.receiver.payloadBuffer = make(map[SeqNum]string)
	b.receiver.mutex = sync.Mutex{}
	return b
}

func (b *Builder) setUpLogger() BuildProcess {
	// remove old log file
	logFileName := "arrival.log"
	_ = os.Remove(logFileName)

	// create the new log file
	arrivalLogFile, err := os.Create(logFileName)
	checkErr(err)
	arrivalLogFile.Sync()
	b.receiver.arrivalLogFile = arrivalLogFile

	b.receiver.arrivalLogger = log.New(arrivalLogFile, "", 0)

	return b
}

func (b *Builder) SetRemoteAddress(remoteIP string, remotePort int) BuildProcess {
	b.receiver.remoteAddr = &net.UDPAddr{
		IP:   net.ParseIP(remoteIP),
		Port: remotePort,
	}
	return b
}

func (b *Builder) SetLocalAddress(localIP string, localPort int) BuildProcess {
	b.receiver.localAddr = &net.UDPAddr{
		IP:   net.ParseIP(localIP),
		Port: localPort, // listen to all local ips
	}
	return b
}

func (b *Builder) SetFileReceived(filename string) BuildProcess {
	// remove old files
	_ = os.Remove(filename)

	// create the new file
	file, err := os.Create(filename)
	checkErr(err)
	file.Sync()
	b.receiver.fileReceived = file
	return b
}

func (b *Builder) setUdpSocket() BuildProcess {
	if b.receiver.localAddr == nil || b.receiver.remoteAddr == nil {
		panic("SetUdpSocket can be called only after SetRemoteAddress and SetLocalAddress")
	}
	udpSocket, err := net.ListenUDP("udp", b.receiver.localAddr)
	checkErr(err)

	b.receiver.udpSocket = udpSocket

	return b
}

func (b *Builder) GetReceiver() RDTReceiver {
	b.setUpLogger().
		setUdpSocket().
		setMisc()
	return b.receiver
}

func checkErr(err error) {
	if err != nil {
		// TODO: delete this
		log.Fatal(err)
	}
}
