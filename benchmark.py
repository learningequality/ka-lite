import sys
from benchmarkclient import BenchmarkClient
from benchmarkserver import BenchmarkingServer
import time
import logging


def benchmark_client(f):
    """decorator function for benchmarkclient.py


    f --  the function that decorator wraps
    The wrapper starts the benchmark server
    and benchmarks the function that decorator is wrapped in
    """
  
    def wrapper(*args, **kwargs):
    
        if '--benchmark' not in sys.argv:
            return f(*args, **kwargs)
        else:
            p2 = BenchmarkingServer(f.__name__)
            p2.start()
            with BenchmarkClient():
                logging.info("inside benchmarkclient decorator")
                #sleep needed because of race condition, server spawns new process
                #before closing old one
                time.sleep(1)
                return f(*args, **kwargs)

    return wrapper

