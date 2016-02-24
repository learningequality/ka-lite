"""
This is the replacement of the old 'chronograph' approach of using the Django
application stack, including database access, to solve concurrent tasks for
KA Lite.

We solve the following tasks:

 - Download videos
 - Look for new videos to download (fired when user submits new data)
 - Sync with the online sync server (TODO)


There are two types of threads:

 - 1 main scheduler thread responsible of managing workers and update the
   job queue.
 - X worker threads, where X is configurable and should reflect bandwidth i/o


.. warning:: Remember that this module is loaded both by kalitectl and by all
             of the WSGI server's workers!**


Reading and writing progress files is done atomically by means of write-replace
pattern. See: https://blog.gocept.com/2013/07/15/reliable-file-updates-with-python/


"""
from __future__ import print_function, absolute_import, unicode_literals

import json
import logging
import os
import shutil
import time
import uuid
from threading import Thread
import traceback

KALITE_HOME = os.environ['KALITE_HOME']

# Workers store their progress files here. Progress is not available after a
# job finishes.
WORKER_SPOOL_DIR = os.path.join(KALITE_HOME, 'spool', 'activity')

# Where to store job feedback
JOB_SPOOL_DIR = os.path.join(KALITE_HOME, 'spool', 'jobs')

# How often to check for new jobs
POLL_INTERVAL_SECONDS = 5

# Maximum workers to start
MAX_WORKERS = 4

logger = logging.getLogger(__name__)


def reset_spool():
    """
    Called each time the main thread starts.

    Resets the output of workers since those are definitely gone since last,
    however we maintain a persistent job spool, so the job description files
    are not purged.
    """
    if os.path.exists(WORKER_SPOOL_DIR):
        shutil.rmtree(WORKER_SPOOL_DIR)
    os.makedirs(WORKER_SPOOL_DIR)
    if not os.path.exists(JOB_SPOOL_DIR):
        os.makedirs(JOB_SPOOL_DIR)


def purge_jobs():
    """
    Purges the job queue
    """
    if os.path.exists(JOB_SPOOL_DIR):
        shutil.rmtree(JOB_SPOOL_DIR)
    os.makedirs(JOB_SPOOL_DIR)

class Scheduler(Thread):
    """
    Main scheduler thread. Detects new jobs in the spool and generates up to
    MAX_WORKERS amount of worker threads for each unsolved job.

    After each job finishes, the job description is removed from the spool.
    """

    def __init__(self, *args, **kwargs):
        # Do this every time so we don't have data of unknown jobs lying around.
        reset_spool()
        super(Scheduler, self).__init__(*args, **kwargs)
        self.setDaemon(True)

    def get_job(self, file_name, cnt):
        """
        Fetch a job from the spool and return a new instance of the job worker
        class

        If reading the description file is somehow unsuccessful, then None is
        returned and error is logged.
        """
        file_path = os.path.join(JOB_SPOOL_DIR, file_name)
        try:
            job_description = open(file_path, 'r').read()
            try:
                JobClass, job_kwargs = parse_job_description(job_description)
                return JobClass(
                    file_path,
                    kwargs=job_kwargs
                )
            except ValueError:
                logging.error("Error reading job: {}".format(file_path))
        except OSError:
            logging.error("Error reading {}".format(file_path))

    def run(self):
        """
        Run the scheduler, picking jobs from the spool, parsing the job
        description file and starting new threads
        """

        active_jobs = {}

        while True:

            # Check all currently running jobs
            finished_jobs = {k: v for k, v in active_jobs.items() if not v.is_alive()}
            active_jobs = {k: v for k, v in active_jobs.items() if v.is_alive()}

            # Finalize jobs that are done
            for job in finished_jobs.values():
                self.finalize_job(job)

            # Check all files containing job descriptions
            new_jobs = filter(lambda f: f not in active_jobs, os.listdir(JOB_SPOOL_DIR))
            for cnt, file_name in enumerate(new_jobs):
                # Never start any more workers than we are allowed
                if cnt + len(active_jobs) >= MAX_WORKERS:
                    break
                job = self.get_job(file_name, cnt)
                if job:
                    job.start()
                    active_jobs[file_name] = job

            time.sleep(POLL_INTERVAL_SECONDS)

    def finalize_job(self, job):
        """
        Calls a jobs finalize method and removes its description from the
        file system spool dir
        """
        try:
            # Callback for the job
            job.finalize()
            # Ensure its progress file is removed
            if os.path.isfile(job.progress_file_path):
                os.remove(job.progress_file_path)
            # Finally, remove the job description from spool
            if os.path.isfile(job.job_file):
                logger.debug("Removing job file: {}".format(job.job_file))
                os.remove(job.job_file)
        except Exception as e:
            logger.error(
                "job {job_id} failed to finalize: {reason}\n\n{traceback}".format(
                    job_id=job.id,
                    reason=str(e),
                    traceback=traceback.format_exc(),
                )
            )


class SingleJobWorker(Thread):
    """
    An instance of this type is spawned for every job that is taken from
    the queue.
    """

    def __init__(self, job_file, *args, **kwargs):
        self.job_file = job_file
        self.id = uuid.uuid4().hex
        self.kwargs = kwargs.pop('kwargs', {})
        self.progress_file_path = os.path.join(WORKER_SPOOL_DIR, self.id + ".json")
        super(SingleJobWorker, self).__init__(*args, **kwargs)
        self.setDaemon(True)

    def run(self):
        raise NotImplementedError()

    def finalize(self):
        """
        A non-concurrent function called by the scheduler when the worker has
        finished its run() method
        """
        return

    def write_progress(self, progress_data):
        """
        Write-rename is not atomic on Windows, so we have to assume that a
        reader can encounter failures while reading the file, and the writer
        may be temporarily denied access while the file is opened by another
        process.

        See:
        http://stackoverflow.com/a/8107434/405682
        http://docs.python.org/library/os.html#os.rename

        If ultimately writing progress fails after a few retries, the old
        progress file will not be overwritten.
        """
        def write_progress_atomic():
            temp_file_path = self.progress_file_path + '.tmp'
            with open(temp_file_path, "w") as f:
                f.write(
                    json.dumps({
                        'id': self.id,
                        'data': progress_data,
                    })
                )
            if os.name == 'nt' and os.path.exists(self.progress_file_path):
                os.remove(self.progress_file_path)
            os.rename(temp_file_path, self.progress_file_path)

        for __ in range(3):
            try:
                write_progress_atomic()
                return True
            except OSError:
                continue
            time.sleep(1)
        logger.error(
            "Max amount of retries exceeded writing progress in {}".format(
                self.progress_file_path
            )
        )
        return False


class VideoDownloader(SingleJobWorker):
    """
    A job used for downloading videos. These jobs are added by the
    VideoDownloadQueueUpdate and by each VideoDownloader's finalize function.

    Rationale: Do not create and manage 10.000 inactive job files, instead only
    have the ones that are active and generate new ones when the active ones
    are successfully done.

    Manual example of downloading 1 video:

    1. Place a file in .kalite/spool/jobs/whatevernameyoulike
    2. Content: {id: 'video_downloader', data: {'id': 'video-id'}}
    """

    def run(self):
        # TODO: Implement video downloading
        pass

    def finalize(self):
        """
        Updates the database after a video is downloaded, fetches the next video
        scheduled for download.
        """
        from kalite.topic_tools.content_models import Item

        # Mark video as available
        Item.update(available=True).where(
            youtube_id=self.kwargs['youtube_id']
        )

        # Fetch next video scheduled for download
        selector = Item.select().where(
            Item.available == False &  # @IgnorePep8
            Item.schedule_download == True
        ).limit(1)

        # Create a job
        for item in selector.execute():
            create_job(JOB_VIDEO_DOWNLOADER, {'youtube_id': item.youtube_id})

        super(VideoDownloader, self).finalize()


class IdleJob(SingleJobWorker):
    """
    A job used for test cases.

    Manual example:

    1. Place a file in .kalite/spool/jobs/your_job_uuid
    2. Content: {id: 'idle', data: {'duration': 123}}
    """

    def run(self):
        logger.info("Starting IdleJob {}".format(self.id))
        duration = int(self.kwargs.get('duration', 10))
        for n in range(duration):
            self.write_progress({'duration': float(n) / float(duration)})
            time.sleep(1)

    def finalize(self):
        logger.info("Finalizing IdleJob {}".format(self.id))
        super(IdleJob, self).finalize()


JOB_VIDEO_DOWNLOADER = 'video_downloader'
JOB_IDLE = 'idle'

JOB_TYPES = {
    JOB_VIDEO_DOWNLOADER: VideoDownloader,
    JOB_IDLE: IdleJob,
}


def parse_job_description(job_description):
    """
    Returns (JobClass, kwargs)

    :param: job_description: input from a job spool file
    """
    job_data = json.loads(job_description)  # raises ValueError
    try:
        return (
            JOB_TYPES.get(job_data.get('type')),
            job_data.get('data', None)
        )
    except KeyError:
        raise ValueError("No job type or illegal job type in job description")


def create_job(job_type, data):
    """
    Create a new job

    :param: job_type: something from JOB_TYPES
    :param: data: Should be JSON serializable
    """
    file_name = uuid.uuid4().hex + ".json"
    with open(os.path.join(JOB_SPOOL_DIR, file_name), "w") as f:
        f.write(
            json.dumps(
                {'type': job_type, 'data': data}
            )
        )


def get_worker_progress_data():
    """
    Returns all available progress data.

    This is not surely the interface for checking up on all jobs, but it could
    well be...
    """
    # For each file in the worker data dir, yield it's content once read
    # successfully
    for file_name in os.listdir(WORKER_SPOOL_DIR):
        # Keep reading the file until something is there or it's gone
        file_path = os.path.join(WORKER_SPOOL_DIR, file_name)
        if not os.path.isfile(file_path) or file_path.endswith('.tmp'):
            continue
        while True:
            try:
                f = open(file_path, 'r')
                yield json.loads(f.read())
                break
            except (OSError, ValueError):
                time.sleep(0.1)
