package rdt_receiver

import (
	"log"
	"net"
	"os"
	"sync"
)

const (
	PacketBytesLen = 512
	WindowSize     = 10
)

type RDTReceiver struct {
	remoteAddr     *net.UDPAddr
	localAddr      *net.UDPAddr
	udpSocket      *net.UDPConn
	fileReceived   *os.File
	arrivalLogger  *log.Logger
	arrivalLogFile *os.File
	globalQuit     chan interface{}
	waitGroup      *sync.WaitGroup
	receiveBase    SeqNum
	payloadBuffer  map[SeqNum]string
	mutex          sync.Mutex
}

func (receiver *RDTReceiver) Start() {
	for {
		select {
		case <-receiver.globalQuit:
			receiver.waitGroup.Wait() // wait for all processing to finish
			receiver.stop()
			return // After EOT has been sent
		default:
			buffer := make([]byte, PacketBytesLen)
			n, _ := receiver.udpSocket.Read(buffer)
			// When n is 0, nothing is in the socket
			if n != 0 {
				receiver.waitGroup.Add(1)
				go receiver.processReceivedBytes(n, buffer)
			}
		}
	}
}

func (receiver *RDTReceiver) stop() {
	receiver.fileReceived.Close()
	receiver.arrivalLogFile.Close()
}

func (receiver *RDTReceiver) isPacketInCurrentWindow(packetSeqNum SeqNum) bool {
	var currentWindowEnd SeqNum

	if receiver.receiveBase <= RingSize-WindowSize {
		// base <= 22; No ring
		currentWindowEnd = SeqNum(receiver.receiveBase + WindowSize - 1)
		return packetSeqNum >= receiver.receiveBase && packetSeqNum <= currentWindowEnd
	} else {
		currentWindowEnd = SeqNum(WindowSize - (RingSize - receiver.receiveBase) - 1)
		return packetSeqNum >= receiver.receiveBase || packetSeqNum <= currentWindowEnd
	}
}

func (receiver *RDTReceiver) isPacketInPreviousWindow(packetSeqNum SeqNum) bool {
	var previousWindowStart SeqNum
	if receiver.receiveBase >= WindowSize {
		// base >= 10; No ring
		previousWindowStart = SeqNum(receiver.receiveBase - WindowSize)
		return packetSeqNum >= previousWindowStart && packetSeqNum < receiver.receiveBase
	} else {
		// packetSeqNum < 10; hit the ring
		previousWindowStart = SeqNum(RingSize - (WindowSize - receiver.receiveBase))
		return packetSeqNum < receiver.receiveBase || packetSeqNum >= previousWindowStart
	}
}

func (receiver *RDTReceiver) processReceivedBytes(byteLen int, buff []byte) {
	// unblock the quit case
	defer receiver.waitGroup.Done()

	packet := decode(buff[:byteLen])
	log.Println(packet)
	if packet.flag == DATA {
		receiver.mutex.Lock()
		// received a data packet
		// Log arrival
		receiver.arrivalLogger.Println(packet.seqNum)

		// if the packet is before the previous window, ignore

		if receiver.isPacketInPreviousWindow(packet.seqNum) {

			receiver.sendAck(packet.seqNum)
			log.Printf("Old Ack packetSeqNum: %d, receiveBase: %d", packet.seqNum, receiver.receiveBase)
		} else if packet.seqNum == receiver.receiveBase {

			receiver.sendAck(packet.seqNum)

			// Store the payload in the buffer
			receiver.payloadBuffer[packet.seqNum] = packet.payload

			// slide the window
			receiver.slideWindow()
			log.Printf("packetSeqNum: %d, receiveBase: %d", packet.seqNum, receiver.receiveBase)
		} else if receiver.isPacketInCurrentWindow(packet.seqNum) {
			// packet is  in the window
			receiver.sendAck(packet.seqNum)

			log.Printf("Gap Ack packetSeqNum: %d, receiveBase: %d", packet.seqNum, receiver.receiveBase)

			// buffer it if not received
			_, presence := receiver.payloadBuffer[packet.seqNum]
			if !presence {
				receiver.payloadBuffer[packet.seqNum] = packet.payload
			}

		}
		receiver.mutex.Unlock()

	} else if packet.flag == EOT || packet.length == 0 {
		// log arrival
		receiver.arrivalLogger.Println("EOT")

		// send EOT packet
		receiver.sendEOT()

		// close listening on the udp socket
		receiver.udpSocket.Close()

		// stop the receiver
		close(receiver.globalQuit)
	}

	// all other packets are mal-formed
}

func (receiver *RDTReceiver) slideWindow() {
	payload, presence := receiver.payloadBuffer[receiver.receiveBase]
	// presence must be true

	for presence {
		// remove the packet from the buffer
		delete(receiver.payloadBuffer, receiver.receiveBase)
		receiver.deliverPayloadToApplication(payload)
		receiver.receiveBase = receiver.receiveBase.Next()
		payload, presence = receiver.payloadBuffer[receiver.receiveBase]
	}
}

func (receiver *RDTReceiver) deliverPayloadToApplication(payload string) {
	// TODO: error handling
	_, err := receiver.fileReceived.WriteString(payload)
	checkErr(err)
	_ = receiver.fileReceived.Sync()
}

func (receiver *RDTReceiver) sendAck(seqNum SeqNum) {
	ackPacket := Packet{
		flag:    SACK,
		seqNum:  seqNum,
		length:  0,
		payload: "",
	}
	receiver.sendPacket(&ackPacket)
}

func (receiver *RDTReceiver) sendEOT() {
	EOTPacket := Packet{
		flag:    EOT,
		seqNum:  0,
		length:  0,
		payload: "",
	}

	receiver.sendPacket(&EOTPacket)

}

func (receiver *RDTReceiver) sendPacket(packet *Packet) {
	bytes := encode(*packet)
	_, err := receiver.udpSocket.WriteToUDP(bytes, receiver.remoteAddr)
	checkErr(err)
}
