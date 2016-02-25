import os
import socket
import time
import logging


class BenchmarkClient(object):
    """This class connects to a benchmarkserver via sockets
    It sends a message to start the benchmarking process, while also
    passing its own pid
    This class is written as a decorator to make it more abstract and portable
    across any code base
    """

    def __init__(self, host="localhost", port=6000):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        for i in range(0, 100):
            time.sleep(.25)
            try:
                self.s.connect((self.host, self.port))
                break
            except socket.error:
                print "failed to connect"
                continue
        self.pid = os.getpid()
        the_string = 'start,{}'.format(self.pid)
        message_len = len(the_string)
        total_sent = 0
        while (total_sent < message_len):
            sent = self.s.send(the_string)
            total_sent += sent
        logging.info("end of start function")

    def stop(self):
        self.s.sendall('close')
        self.s.close()

    def __enter__(self):
        logging.info("inside client start")
        self.start()

    def __exit__(self, exception_type, exception_val, trace):
        logging.info("inside client stop")
        try:
            self.stop()
        except AttributeError:
            print "attribute error"
