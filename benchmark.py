import psutil
import multiprocessing


class BenchmarkingProcess(multiprocessing.Process):
    """
    Receive messages from the main kalite process on whether to start or stop tracking, and how often.

    Write the results in a file.
    """

    """

    when flag is passed,create BenchmarkingThread object and call start_benchmark function
    timer function will be inside this flag too, or can be its own seperate flag
    benchmark writes to file, appending to it instead of overwriting the previous benchmark 
    call stop benchmark to end benchmark,
    call kill process after its finished???
    """


    def __init__(self, pid, ipc):
        self.Benchmarking = True
        self.pid = pid
        self.ipc = ipc
        super(BenchmarkingProcess, self).__init__()
        #multiprocessing.Process.__init__(self)

    def run():
        while True:
            msg = get_message()
            if msg == "start":
                _start_benchmark()
            elif msg == "stop":
                break
            else:
                continue

    def start_benchmark(self):
        self.ipc.add('start')

    def stop_benchmark(self):
        self.ipc.add('stop')   

    def _start_benchmark(self):
        process = psutil.Process(self.pid)
        f = open('benchmarkresults',"a")
        cpu_usage = psutil.cpu_percent(percpu=True)
        mem_usage = process.get_memory_info()[0] / float(2 ** 20)
    #   disk_io = psutil.disk_usage(path)
        benchmark_values = '{}\n'.format(cpu_usage)
        f.write(benchmark_values)
        f.close()

    def get_message(self):
        self.ipc.pop(0)

   

