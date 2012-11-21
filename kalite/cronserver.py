import threading, subprocess

def cron():
    subprocess.call(["python", "manage.py", "cron"])
    threading.Timer(5, cron).start()

if __name__ == "__main__":
    cron()