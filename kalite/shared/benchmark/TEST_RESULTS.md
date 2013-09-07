## Benchmark tests and results

### I/O performance benchmarks

#### Generate real data

This benchmark empties the database and then runs generaterealdata.  This benchmark measures I/O insert performance, and, to a lesser extent computation power.

* RaspberryPi benchmark result: **1.5 records per second**
* Intel E5500/Sata/3gb ram comparison: **2.7 records per second**

```
./stop.sh
./kalite/manage.py shell
>>> import benchmark.benchmark_test_cases as btc
>>> btc.GenerateRealData().execute()
```

#### One thousand random reads

Using the database created by *Generate real data*, tests data reading speed from the VideoLog and ExerciseLog models.

This benchmark measures SELECT speed and will probably use cached reads if enough memory is available.

* RaspberryPi benchmark result: **21.6 records per second**
* Intel E5500/Sata/3gb ram comparison: **410 records per second**

```
$./stop.sh
$./kalite/manage.py shell
>>> import benchmark.benchmark_test_cases as btc
>>> btc.OneThousandRandomReads().execute()
```

#### One hundred random log updates

Using the database created by *Generate real data*, this benchmark tests updating the VideoLog and ExerciseLog models.

This benchmark principally measures UPDATE speed and will normally generate physical I/O

* RaspberryPi benchmark result: **1.8 records per second**
* Intel E5500/Sata/3gb ram comparison: **2.9 records per second**

```
$./stop.sh
$./kalite/manage.py shell
>>> import benchmark.benchmark_test_cases as btc
>>> btc.OneHundredRandomLogUpdates().execute(iterations=5)
```

#### One hundred random log updates commit success

Same as above, but all one hundred updates are done in a sigle transaction
and should be quicker 

* RaspberryPi benchmark result: **2.0 records per second**
* Intel E5500/Sata/3gb ram comparison: **5.3 records per second**

```
$./stop.sh
$./kalite/manage.py shell
>>> import benchmark.benchmark_test_cases as btc
>>> btc.OneHundredRandomLogUpdatesSingleTransaction().execute(iterations=5)


```

#### Login Logout

This benchmark tests the login performance of a raspberry pi as a distributed server.  The test measures time taken
for a student to get from the landing page, through login and to get to the home page.

Additional competing login tasks are added to measure how the server responds to increasing login requests.


This benchmark has high CPU usage - expect the Raspberry Pi to be 100% busy with more than 3 competing logins.

* RaspberryPi benchmark result: [number of competing logins, time taken to login]*

**0 competing  2.05 seconds**

**1 competing 	2.04 seconds**

**2 competing 	2.55 seconds**

**3 competing 	2.29 seconds**

**4 competing 	3.69 seconds**

**5 competing 	4.06 seconds**

**6 competing 	5.44 seconds**

**7 competing 	6.52 seconds**

**8 competing 	9.27 seconds**

**9 competing 	10.83 seconds**

...


**14 competing 	16.15 seconds**


The raspberry Pi is acting as distributed server; another desktop machine runs **only one** script to test the timings.
Several additional desktops run the same test continuously.  Each desktop can probably run 5 to 7 concurrent
scripts, but the scripts will become unstable if too much load is applied.  The test is re-run multiple times,
each time an additional script was started to progressively build up the load on the raspberry Pi server.

**Configuration:** 
Raspberry Pi distributed server with a student login created
Raspberry Pi wired into wireless router
3x desktops, wireless connected to router, and loaded with ka-lite (server NOT running on these machines)

**Test:** 
1x desktop begins by running the login/logout script.  This desktop will always run one instance of this script.

```
$ ./kalite/manage.py shell
>>> import benchmark.benchmark_test_cases as btc
>>> btc.LoginLogout(url="http://192.168.x.x:8008", username="foo", password="bar").execute(iterations=5)

```

On a separate desktop machine, startup a competing login (using the same script).  This time, set the iterations
to say 1000 so the process runs continuously.  Note: the Selenium script may give a timeout to the console once 
the desktop becomes stressed.  Just restart these failed processes.  It is important to monitor the competing 
processes because the benchmark will not be valid if some of the competing load has timed-out.


```
$ ./kalite/manage.py shell
>>> import benchmark.benchmark_test_cases as btc
>>> btc.LoginLogout(url="http://192.168.x.x:8008", username="foo", password="bar").execute(iterations=1000)

```

Expect a typical desktop to support about 5-10 competing logins, but with the occassional timeout.



