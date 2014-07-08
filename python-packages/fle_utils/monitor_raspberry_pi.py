import getopt
import os
import platform
import time
import sys
"""
Very simple monitoring for the Raspberry Pi, useful for benchmarks.
Samples selected parameters, and writes them to stdout

CPU loads are delta changes over a 5 second duration
  so the minimum interval for monitoring is 6 seconds
All other outputs are instantaneous values

Sleep timers in python won't be 100% accurate, but good enough

usage...
$python monitor_raspberry_pi.py --interval=10, --duration=0 &

All parameters optional; by default will output every 10 seconds forever.
Just pipe the output to a file of your choice.

To stop, just kill it
"""

def get_temp():
    if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
        res = open('/sys/class/thermal/thermal_zone0/temp', 'r')
        val = res.readline()
        res.close()
        return int(val)/1000.
    else:
        return 0

def get_cpu():
    res = open('/proc/stat', 'r')
    val = res.readline()
    res.close()
    stringlist = (val.replace("cpu", "").split())
    return [int(i) for i in stringlist]

def ram_used():
    res = open('/proc/meminfo', 'r')
    total = res.readline()
    free = res.readline()
    res.close()
    totsplit = total.split()
    freesplit = free.split()
    return 100-(int(freesplit[1])*1.0/int(totsplit[1])*100)

def main(interval, duration):
    end_time = time.time() + duration if duration > 0 else 99999999999
    sys.stdout.write("\n")
    
    while time.time() < end_time:
        cpu_before = get_cpu()
        time.sleep(5)
        cpu_after = get_cpu()
        cpu_change = [(after-before) for after, before in zip(cpu_after, cpu_before)]
        cpu_stat = (100-(cpu_change[3]/(sum(cpu_change)*1.0))*100.)
        iowait_stat = (cpu_change[4]/(sum(cpu_change)*1.0)*100.)

        sys.stdout.write(('%s "Temp" %.2f "RAM used" %.2f "Total CPU" %.2f "Waiting IO" %.2f \n' ) % (time.strftime('%X'), get_temp(), ram_used(), cpu_stat, iowait_stat, ))
        time.sleep(interval-5)


if platform.system() == 'Windows':
    raise Exception("errrr nothing to see here")

if __name__ == "__main__":

    interval = 10
    duration = 0
    opts, args = getopt.getopt(sys.argv[1:], "i:d:", ["interval=", "duration="])
    
    for opt, arg in opts:       
        if opt in ("-i", "--interval"):
            interval = int(arg)
        elif opt in ("-d", "--duration"):
            until = int(arg)
            
    assert interval > 6, "interval must be > 6"
    assert duration >= 0, "duration must be zero or greater"
    
    main(interval=interval, duration=duration)