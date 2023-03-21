package rdt_receiver

const RingSize = 32

/*
The SeqNum can only be a integer between [0, 31]
*/
type SeqNum uint32

func (seqNum SeqNum) Next() SeqNum {
	if seqNum == 31 {
		return SeqNum(0)
	}
	return SeqNum(uint64(seqNum) + 1)
}

func GetSeqNumFrom(packetID int) SeqNum {
	return SeqNum(packetID % 32)
}

// GetRingDistance Return the positive ring distance between this and other
// Examples: 31 to 4 = 5; 4 to 31
func (this SeqNum) GetRingDistance(other SeqNum) int {
	difference := int(other - this)
	if difference < 0 {
		return RingSize + difference
	}
	return difference
}
