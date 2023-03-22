import argparse
import queue
import threading
import socket
from queue import Queue

from constants import INITIAL_WINDOW_SIZE, SACK, EOT, PACKET_BYTE_LEN, MAX_WINDOW_SIZE, RING_SIZE, DATA, \
    PAY_LOAD_BYTE_LEN, EVENT_TIMEOUT, EVENT_PACKET_RECEIVED, EVENT_QUEUE_SIZE, SENDING_WAITING_TIME
from logger import LoggerTimeStamped
from packet import Packet, get_next_seq_num


class Sender:
    EOT_received_event = threading.Event()
    EOT_sent_event = threading.Event()
    # Set up loggers
    seq_num_logger = LoggerTimeStamped("seqnum")
    N_logger = LoggerTimeStamped("N")
    ack_logger = LoggerTimeStamped("ack")

    def __init__(self, forward_recv_address, forward_recv_port, sender_recv_port, max_timeout, filename_to_send,
                 verbose=True):
        self.verbose = verbose
        self.filename_to_send = filename_to_send
        self.remote_addr = (forward_recv_address, forward_recv_port)
        self.local_addr = ("", sender_recv_port)
        self.max_timeout = max_timeout / 1000.0  # max timeout the timer will wait after sending the packet
        self.window_size = INITIAL_WINDOW_SIZE
        self.timestamp = 0
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(self.local_addr)
        self.receiving_thread = threading.Thread(target=self.receive_packets)
        self.data_pointer = 0
        self.data = []
        self.set_data()
        self.send_base = 0
        self.next_seq_num = 0
        self.packets_sent = {}
        self.timers = {}
        self.packets_timed_out = []
        self.acked_packets = []
        self.event_queue = Queue(EVENT_QUEUE_SIZE)

    def set_data(self):
        with open(self.filename_to_send, 'r') as file:
            payload = file.read(PAY_LOAD_BYTE_LEN)

            if payload == "":
                self.data.append(payload)  # sender the empty file
            else:
                while payload != "":
                    self.data.append(payload)
                    payload = file.read(PAY_LOAD_BYTE_LEN)

    def __str__(self):
        return "RDT Sender Info: \n" + \
            f"Listening on local addr: {self.local_addr}\n" + \
            f"Will send packets to {self.remote_addr}\n" + \
            f"Will Send file: {self.filename_to_send} \n" + \
            f"Number of Packets: {len(self.data)}\n" + \
            f"Will retransmit packet after {self.max_timeout} ms\n"

    def start(self):
        self.receiving_thread.start()

        while not self.EOT_received_event.is_set():
            try:
                event = self.event_queue.get(block=True, timeout=SENDING_WAITING_TIME)
                if event[0] == EVENT_TIMEOUT:
                    packet_seq_num = event[1]
                    self.on_time_out(packet_seq_num)
                elif event[0] == EVENT_PACKET_RECEIVED:
                    packet_buff = event[1]
                    self.process_received_packets(packet_buff)
            except queue.Empty:
                self.delayed_retransmit_all_timed_out_packets_in_window()
                self.send_new_packet()

        self.receiving_thread.join()
        self.close()

    def delayed_retransmit_all_timed_out_packets_in_window(self):
        for packet_seq_num in self.packets_timed_out:
            self.delayed_retransmit_packet_timed_out(packet_seq_num)

    def put_timeout_event_in_event_queue(self, packet_seq_num):
        event_timed_out = (EVENT_TIMEOUT, packet_seq_num)
        self.event_queue.put(event_timed_out)

    def send_data_packet_start_timer(self, packet):
        buffer = packet.encode()
        self.udp_socket.sendto(buffer, self.remote_addr)
        timer = threading.Timer(self.max_timeout, self.put_timeout_event_in_event_queue, args=(packet.seqnum,))
        timer.daemon = True
        timer.start()
        self.timers[packet.seqnum] = timer

    def send_new_packet(self):
        if self.is_next_seq_num_in_window() and self.has_packets_to_send():
            data = self.get_next_data()
            packet = Packet(DATA, self.next_seq_num, len(data), data)
            self.send_data_packet_start_timer(packet)
            self.increase_next_seq_num_by_one()
            if self.verbose:
                print(f"Sending New Packet: \n {packet}")
                print(f"Timestamp: {self.timestamp}")
            self.on_sent_new_packet(packet.seqnum)
            self.packets_sent[packet.seqnum] = packet  # for retransmission

    def delayed_retransmit_packet_timed_out(self, packet_seq_num):
        if self.is_seq_num_in_window(packet_seq_num):
            packet = self.packets_sent[packet_seq_num]
            self.send_data_packet_start_timer(packet)
            if self.verbose:
                print(f"Delayed Retransmission Packet: \n {packet}")
                print(f"Timestamp: {self.timestamp}")
            self.on_delayed_retransmission(packet_seq_num)

    def is_next_seq_num_in_window(self):
        return self.is_seq_num_in_window(self.next_seq_num)

    def is_seq_num_in_window(self, seq_num):
        if self.send_base <= RING_SIZE - self.window_size:
            window_end_seq_num = self.send_base + self.window_size - 1
            return self.send_base <= seq_num <= window_end_seq_num
        else:
            window_end_seq_num = self.window_size - 1 - (RING_SIZE - self.send_base)
            # hit the ring
            return seq_num >= self.send_base or seq_num <= window_end_seq_num

    def has_packets_to_send(self):
        return self.data_pointer <= len(self.data) - 1

    # for every event, log the window size and increment the time stamp
    def on_EOT_received(self):

        if self.verbose:
            print(f"Received EOT Packet at timestamp {self.timestamp}.")
        self.ack_logger.log(self.timestamp, "EOT")
        self.N_logger.log(self.timestamp, self.window_size)
        self.timestamp += 1

    def on_duplicate_ack_received(self, packet_seq_num):

        self.ack_logger.log(self.timestamp, packet_seq_num)
        self.N_logger.log(self.timestamp, self.window_size)
        self.timestamp += 1

    def on_new_ack_received(self, packet_seq_num):

        self.ack_logger.log(self.timestamp, packet_seq_num)
        self.increase_window_size_by_one()

        self.N_logger.log(self.timestamp, self.window_size)
        self.timestamp += 1

    def on_sent_new_packet(self, packet_seq_num):

        self.seq_num_logger.log(self.timestamp, packet_seq_num)
        self.N_logger.log(self.timestamp, self.window_size)
        self.timestamp += 1

    def on_delayed_retransmission(self, packet_seq_num):

        self.seq_num_logger.log(self.timestamp, packet_seq_num)
        self.N_logger.log(self.timestamp, self.window_size)
        self.timestamp += 1

    def on_time_out(self, packet_seq_num):
        # check if ack event arrives before the timeout event
        # else the packet is already acked
        if self.is_packet_not_acked(packet_seq_num):
            # stop sending
            self.window_size = 1
            self.N_logger.log(self.timestamp, self.window_size)
            if self.verbose:
                print(f"Time-out Packet Seqnum: {packet_seq_num}")
                print(f"Timestamp: {self.timestamp}")

            # check for immediate retransmission
            if packet_seq_num == self.send_base:
                packet = self.packets_sent[packet_seq_num]
                self.send_data_packet_start_timer(packet)
                self.seq_num_logger.log(self.timestamp, packet_seq_num)
                if self.verbose:
                    print(f"Immediate Retransmission Packet Seqnum: \n {packet}")
                    print(f"Timestamp: {self.timestamp}")
            else:
                self.packets_timed_out.append(packet_seq_num)
                print(f"Wait for Delayed Retransmission Packet Seqnum:  {packet_seq_num}")
                print(f"Timestamp: {self.timestamp}")
            self.timestamp += 1

    def increase_window_size_by_one(self):

        if self.window_size < MAX_WINDOW_SIZE:
            self.window_size += 1
        else:
            self.window_size = MAX_WINDOW_SIZE

    def send_EOT(self):
        self.EOT_sent_event.set()
        packet = Packet(EOT, 0, 0, "")
        buffer = packet.encode()
        sender.udp_socket.sendto(buffer, self.remote_addr)
        self.on_EOT_sent()

    def on_EOT_sent(self):

        if self.verbose:
            print(f"Sent EOT at timestamp {self.timestamp}.")
        self.seq_num_logger.log(self.timestamp, "EOT")
        self.N_logger.log(self.timestamp, self.window_size)
        self.timestamp += 1

    def receive_packets(self):
        if self.verbose:
            print("Starting Receiving Packets")
        while not self.EOT_received_event.is_set():
            try:
                packet_buffer = self.udp_socket.recv(PACKET_BYTE_LEN)
                event_packet_received = (EVENT_PACKET_RECEIVED, packet_buffer)
                self.event_queue.put(event_packet_received)
            except socket.error:
                pass  # the end of the transaction

        if self.verbose:
            print("Receiving Packets Thread Stopped")

    def process_received_packets(self, buffer):
        if not isinstance(buffer, bytes):
            raise RuntimeError("processPacket can only process a packet encoded as bytes")
        packet = Packet(buffer)
        typ, seqnum, length, data = packet.decode()

        if typ == SACK:
            self.process_ack_packet(packet.seqnum)
            if self.areAllPacketsAcked():
                sender.send_EOT()
        if typ == EOT:
            self.on_EOT_received()
            if self.areAllPacketsAcked() and self.EOT_sent_event.is_set():
                self.EOT_received_event.set()  # Stop the receiving thread
                sentinel_packet = Packet(DATA, 0, 0, "")
                self.udp_socket.sendto(sentinel_packet.encode(), self.local_addr)  # sentinel
                self.udp_socket.close()

    def close(self):
        self.seq_num_logger.close()
        self.ack_logger.close()
        self.N_logger.close()

    def process_ack_packet(self, packet_seq_num):
        # block sending
        if self.is_packet_not_acked(packet_seq_num):
            if self.verbose:
                print(f"Received New ACK Packet at timestamp {self.timestamp}; Packet Seq Num :{packet_seq_num}")
            self.on_new_ack_received(packet_seq_num)

            # Stop the timer
            timer = self.timers[packet_seq_num]
            timer.cancel()

            if self.send_base == packet_seq_num:
                self.slide_window()
            else:
                self.acked_packets.append(packet_seq_num)
        else:
            if self.verbose:
                print(f"Received Duplicate ACK Packet at timestamp {self.timestamp}; Packet Seq Num :{packet_seq_num}")
            self.on_duplicate_ack_received(packet_seq_num)

    def is_packet_not_acked(self, packet_seq_num):
        return self.is_seq_num_in_max_window(packet_seq_num) and packet_seq_num not in self.acked_packets

    def slide_window(self):
        self.acked_packets.sort()
        while len(self.acked_packets) != 0 and self.acked_packets[0] == get_next_seq_num(self.send_base):
            self.send_base = self.acked_packets[0]
            self.acked_packets.remove(self.acked_packets[0])
        self.send_base = get_next_seq_num(self.send_base)  # the next unacked packet

    def is_seq_num_in_max_window(self, packet_seq_num):
        if self.send_base <= RING_SIZE - MAX_WINDOW_SIZE:
            max_window_end = self.send_base + MAX_WINDOW_SIZE - 1
            return self.send_base <= packet_seq_num <= max_window_end
        else:
            max_window_end = MAX_WINDOW_SIZE - 1 - (RING_SIZE - self.send_base)
            return packet_seq_num <= max_window_end or packet_seq_num >= self.send_base

    def areAllPacketsAcked(self):
        return self.send_base == self.next_seq_num and self.data_pointer == len(self.data)

    def get_next_data(self):
        payload = self.data[self.data_pointer]
        self.data_pointer += 1
        return payload

    def increase_next_seq_num_by_one(self):
        self.next_seq_num = get_next_seq_num(self.next_seq_num)


if __name__ == '__main__':
    # Parse Args
    parser = argparse.ArgumentParser(description="the RDTSender module for the RDP protocol")
    parser.add_argument(dest="forward_recv_address", type=str, help="host address of the network emulator")
    parser.add_argument(dest="forward_recv_port", type=int, help="UDP port number used by the RDTSender to receiver "
                                                                 "SACKs"
                                                                 "from the emulator")
    parser.add_argument(dest="sender_recv_port", type=int, help="UDP port number used by the RDTSender to receiver "
                                                                "SACKs"
                                                                "from the emulator")
    parser.add_argument(dest="max_timeout", type=int, help="timeout interval in units of millisecond")
    parser.add_argument(dest="filename", type=str, help="name of the file to be transferred")

    args = parser.parse_args()

    sender = Sender(args.forward_recv_address,
                    args.forward_recv_port,
                    args.sender_recv_port,
                    args.max_timeout,
                    args.filename, True)

    if sender.verbose:
        print("Starting RDTSender....")
        print(sender)

    sender.start()
