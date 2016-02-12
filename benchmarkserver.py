import multiprocessing
import psutil
import socket
import datetime
import time
import csv



class BenchmarkingServer(multiprocessing.Process):

    """This class inheirits from the multiprocessing class
    
    Its purpose is to record and benchmark the connected the client 
    that is connected via sockets
    Data is written to benchmark.csv, which records Date, CPU Usage and Memory Usage
    The server can listen up to 5 queued connections
    """
 

    def __init__(self):
        super(BenchmarkingServer, self).__init__()

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 6000))
        s.listen(5)
        conn,address = s.accept()
        conn.setblocking(0)
        msg = conn.recv(2048)
        msg = msg.split(",")

        if msg[0] == 'start':
            f = open('benchmarkresults.csv',"at")
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(('Date', 'CPU', 'Mem'))
           
            pid = int(msg[1])
            process = psutil.Process(pid)  
            while True:
                cpu_usage = psutil.cpu_percent(percpu=True)
                mem_usage = process.memory_info()[0] / float(2 ** 20)
                #disk_io = psutil.disk_usage(path)
                writer.writerow((datetime.datetime.now(), cpu_usage, mem_usage))
                try:
                    msg = conn.recv(2048)
                    print msg
                except:
                    continue
                if msg == 'close':
                    f.close()
                    conn.close()
                    break
            listener.close()

if __name__ == "__main__":
    pass
        
