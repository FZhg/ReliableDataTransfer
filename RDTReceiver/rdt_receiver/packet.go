package rdt_receiver

import (
	"encoding/binary"
)

const (
	SACK = 0
	DATA = 1
	EOT  = 2
)

type Packet struct {
	flag    uint32 // the type of packet, 0 = ACK, 1 = data, 2 = EOT
	seqNum  SeqNum
	length  uint32 // the length of characters in data AT MOST 500
	payload string
}

func encode(packet Packet) []byte {
	// Use Big Endian to conform with the network byte order
	flagBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(flagBytes, packet.flag)

	seqNumBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(seqNumBytes, uint32(packet.seqNum))

	lengthBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(lengthBytes, packet.length)

	payloadBytes := []byte(packet.payload)

	header := append(flagBytes, seqNumBytes...)
	header = append(header, lengthBytes...)
	packetEncoded := append(header, payloadBytes...)
	return packetEncoded
}

func decode(buffer []byte) Packet {
	var packet Packet
	flagBytes := buffer[:4]
	packet.flag = binary.BigEndian.Uint32(flagBytes)

	seqNumBytes := buffer[4:8]
	packet.seqNum = SeqNum(binary.BigEndian.Uint32(seqNumBytes))

	lengthBytes := buffer[8:12]
	packet.length = binary.BigEndian.Uint32(lengthBytes)

	packet.payload = string(buffer[12:])

	return packet
}
