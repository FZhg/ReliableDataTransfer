"""
A simple logger for writing  arrival.log.
It will create a log file at its creation.
TODO: add multithreading
"""
import os


class Logger:
    """
    :param logger_name should be a string like "seqnum"
    It will remove old logfile and  create a logger file named <logger_name>.log.
    """

    def __init__(self, logger_name):
        log_filename = logger_name + ".log"
        # delete old log file
        if os.path.exists(log_filename):
            os.remove(log_filename)
        self.file = open(log_filename, "w")

    def log(self, message):
        whole_message = f'{message}\n'
        self.file.write(message)
        self.file.flush()

    def close(self):
        self.file.close()


"""
A simple logger for writing seqnum.log, ack.log, N.log.
The log looks like  "t=x 12".
"""


class LoggerTimeStamped(Logger):
    def __init__(self, logger_name):
        super().__init__(logger_name)

    def log(self, time_stamp, message):
        whole_message = f"t={time_stamp} {message}\n"
        super().log(whole_message)
