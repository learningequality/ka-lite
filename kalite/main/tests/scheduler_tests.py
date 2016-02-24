import logging
import time

from unittest2.case import TestCase

from kalite import scheduler

logger = logging.getLogger(__name__)

class IdleTester(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        scheduler.purge_jobs()
        scheduler_t = scheduler.Scheduler()
        scheduler_t.start()

    def test_jobs(self):

        scheduler.MAX_WORKERS = 5
        scheduler.POLL_INTERVAL_SECONDS = 0.1

        for __ in range(10):
            scheduler.create_job(scheduler.JOB_IDLE, {'duration': 2})

        # Wait for 2 seconds
        time.sleep(1)

        # Assure that we can get progress
        progress = scheduler.get_worker_progress_data()

        for job in progress:
            logger.info('Testing scheduler progress after 1 seconds {}'.format(str(job)))

        logger.info("Waiting another 4 seconds and checking that jobs are done")

        time.sleep(4)

        self.assertEqual(
            list(scheduler.get_worker_progress_data()), []
        )
