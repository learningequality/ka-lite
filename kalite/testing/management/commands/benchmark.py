"""
Run benchmarks from the benchmark command
"""
import threading
import time
from functools import partial
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from ...benchmark.test_cases import *


class BenchmarkThread(threading.Thread):
    def __init__(self, fn, threadID, outfile):
        super(BenchmarkThread, self).__init__()
        self.fn = fn
        self.threadID = threadID
        self.outfile = outfile

    def run(self):
        print "Starting (%d)" % self.threadID
        rv = self.fn()
        with open(self.outfile, "a") as fp:
            fp.write("%s\n" % rv["average_elapsed"])
        print "Average elapsed (%d): %s" % (self.threadID, rv["average_elapsed"])
        print "Exiting (%d)" % self.threadID


class Command(BaseCommand):
    help = "Benchmarking.  Choose from: loginlogout, seleniumstudent, generatedata, 1000reads, 100updates, and more!"

    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--clients',
            action='store',
            dest='nclients',
            default=1,
            help='# of simultaneous clients to run',
        ),
        make_option(
            '-t', '--iterations',
            action='store',
            dest='niters',
            type="int",
            default=1,
            help='# of times to repeat the benchmark',
        ),

        make_option(
            '--comment',
            action='store',
            dest='comment',
            default="",
            help='Comment',
        ),
        make_option(
            '--username',
            action='store',
            dest='username',
            default=None,
            help='username (default: benchmark_xx)',
        ),
        make_option(
            '--password',
            action='store',
            dest='password',
            default=None,
            help='password (default: benchmark_xx)',
        ),
        make_option(
            '--url',
            action='store',
            dest='url',
            default="http://localhost:8008/",
            help='URL (default: localhost)',
        ),
        make_option(
            '--starttime',
            action='store',
            dest='starttime',
            default="00:00",
            help='starttime',
        ),
        make_option(
            '--duration',
            action='store',
            dest='duration',
            type="int",
            default=2,
            help='starttime',
        ),
        make_option(
            '--profile',
            action='store',
            dest='behavior_profile',
            default=24601,
            help='profile (i.e. random seed)',
        ),
        make_option(
            '--file',
            action='store',
            dest='out_file',
            default="benchmark_results.txt",
            help='Benchmark output file',
        ),
    )

    class_map = {
        "loginlogout": LoginLogout,
        "seleniumstudent": SeleniumStudentExercisesOnly,
        "ss_classic": SeleniumStudent,
        "generatedata": GenerateRealData,
        "1000reads": OneThousandRandomReads,
        "100updates": OneHundredRandomLogUpdates,
        "100updates_transact": OneHundredRandomLogUpdatesSingleTransaction,
        "helloworld": HelloWorld,
        "validate": ValidateModels,
    }

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError("Must specify the benchmark type.")

        print "Running %s %s times in %s clients" % (args[0], options["niters"], options["nclients"])

        # Choose the benchmark class, based on the input string
        if args[0] in self.class_map:
            cls = self.class_map[args[0]]
        else:
            raise CommandError("Unknown test case: %s;\nSelect from %s" % (args[0], self.class_map.keys()))


        # Now, use the class to make a lambda function
        good_keys = list(set(options.keys()) - set(["niters", "nclients", 'settings', 'pythonpath', 'traceback']))

        # Create the threads (takes time, so call start separately),
        #   passing the lambda function
        threads = []
        for ti in range(int(options["nclients"])):

            # Eliminate unnecessary keys
            kwargs = dict((k, options[k]) for k in good_keys)
            kwargs["behavior_profile"] += ti  # each thread has a different behavior

            # Get username
            kwargs["username"] = kwargs["username"] or "benchmark_%d" % ti
            kwargs["password"] = kwargs["password"] or "benchmark_pass"

            # Now, use the class to make a lambda function
            #   Since each thread can have a different user and profile,
            #
            fn = partial(lambda kwargs: cls(**kwargs).execute(iterations=options["niters"]), kwargs=kwargs)

            th = BenchmarkThread(
                threadID=ti,
                outfile=kwargs["out_file"],
                fn=fn,
            )
            threads.append(th)

        # Run the threads
        for th in threads:
            time.sleep(3)
            th.start()
