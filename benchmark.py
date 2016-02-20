import sys
from benchmarkclient import BenchmarkClient
from benchmarkserver import BenchmarkingServer




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
            with BenchmarkClient() as c:
                return f(*args, **kwargs)

    return wrapper

