import os
import socket
import time




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
    for i in range(0,100):
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

        
  

  def stop(self):
    self.s.send('close')
    self.s.close()

  def __enter__(self):
    self.start()

  def __exit__(self, exception_type, exception_val, trace):
    try:
      self.stop()
    except AttributeError:
      print "attribute error"



