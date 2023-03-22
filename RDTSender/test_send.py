from unittest import TestCase

from RDTSender.send import Sender


class TestSender(TestCase):
    def test_slide_window(self):
        sender = Sender("", 12, 13, 12, "fileSent8Packets.txt")
        sender.acked_packets = [24, 25, 26, 27, 28, 29, 30, 31, 0]
        sender.send_base = 23
        sender.slide_window()
        assert sender.send_base == 1
