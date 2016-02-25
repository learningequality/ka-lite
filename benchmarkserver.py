import multiprocessing
import psutil
import socket
import datetime
import csv
import subprocess
import os.path
import logging
import time

class BenchmarkingServer(multiprocessing.Process):
    """This class inheirits from the multiprocessing class
    Its purpose is to record and benchmark the connected the client
    that is connected via sockets
    Data is written to benchmark.csv, which records Date, CPU Usage and Memory Usage
    The server can listen up to 5 queued connections
    """

    def __init__(self,view_name):
        self.view_name = view_name
        super(BenchmarkingServer, self).__init__()

    def run(self):
        msg, conn = self.connect()
        msg = msg.split(",")
        if msg[0] == 'start':
            f, process, writer = self.writeheader(msg)
            while True:
                self.benchmark(process, writer,f)
                try:
                    msg = conn.recv(2048)
                except:
                    continue
                if msg == 'close':
                    logging.info("inside server close")
                    f.close()
                    conn.close()
                    break
    
    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 6000))
        s.listen(1)
        conn, address = s.accept()
        conn.setblocking(0)
        #printing connect these 2 strings seems to have solved the problem....
        logging.info("inside connect")
        logging.info(conn)
        #sleep here because data was not being retrieved/assigned fast enough
        #which was throwing a resource error
        time.sleep(1)
        return conn.recv(2048), conn
    
    def benchmark(self, process, writer,f):
        cpu_usage_single = psutil.cpu_percent()
        mem_usage = process.memory_info()[0] / float(2 ** 20)
        # disk_io = psutil.disk_usage(path)
        writer.writerow((datetime.datetime.now(), cpu_usage_single, mem_usage))
        f.flush()

    def writeheader(self,msg):
        command = ['git', 'log', '-1', '--format="%H"']
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None)
        hash_file_name = p.stdout.read()
        hash_file_name = hash_file_name[1:-2] + "-" + self.view_name + ".csv" #stdout from pipe adds a whitespace at the end of string
        pid = int(msg[1])
        process = psutil.Process(pid)
        if os.path.isfile(hash_file_name):
            f = open(hash_file_name, "at")
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            return f, process, writer
        else:
            f = open(hash_file_name, "at")
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(('Date', 'CPU', 'Mem'))
            return f, process, writer



if __name__ == "__main__":
    pass
