""" Individual benchmark test cases

    Each benchmark is coded as a separate class

    an _execute method must be specified, this method
    is the actual test which needs to be timed in the benchmark.

    The _execute method can be called >1 time per run
     so it is important that the _execute method is normally re-runnable
     To force a method as not re-runnable,
      set self.max_iterations = 1 in _setup or _execute method

    optional _setup and _teardown methods will be called
     before and after the test, but these methods will not
     affect the benchmark timings

    EXAMPLE USAGE:

    $ ./manage.py shell

    >>> import shared.benchmark.test_cases as btc
    >>> btc.Hello_world(comment="text", fixture="/foo/bar.json").execute(iterations=2)

    IMPORTANT: the fixture argument does NOT install the fixture - this argument
     is only used to record the fixture name in the result dictionary

    example result_dict:

{
'comment': 'some text',
'head': 'f11cf0e Merge pull request #247 from gimick/autostart_on_linux',
'individual_elapsed': {1: 7.616177082061768, 2: 7.196689128875732},
'iterations': 2,
'fixture': '/foo/bar.json',
'average_elapsed': 7.40643310546875,
'uname': ('Linux', 'xubuntu', '3.2.0-35-generic', '#55-Ubuntu SMP Wed Dec 5 17:42:16 UTC 2012', 'x86_64', 'x86_64'),
'branch': 'benchmark_v2',
'class': 'Hello_world'
}
 """
import time
import datetime

from django.conf import settings; logging = settings.LOG
from django.core import management
from django.db import transaction
from selenium.webdriver.support import expected_conditions, ui
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from . import base
from kalite.facility.models import Facility, FacilityUser, FacilityGroup
from kalite.main.models import ExerciseLog, VideoLog, UserLog
from kalite.topic_tools import get_node_cache


class HelloWorld(base.Common):

    def _execute(self):
        wait_time = 10. * self.random.random()
        print "Waiting %ss" % wait_time
        time.sleep(wait_time)

    def _get_post_execute_info(self):
        return "Hello world has finished"


class ValidateModels(base.Common):

    def _execute(self):
        management.call_command('validate', verbosity=1)


class GenerateRealData(base.Common):
    """
    generaterealdata command is both i/o and moderately cpu intensive
    The i/o in this task is primarily INSERT
    Note: if more excercises or videos are added, this benchmark will
    take longer!
    """

    def _setup(self, **kwargs):
        super(GenerateRealData, self)._setup(**kwargs)

        self.max_iterations = 1
        #management.call_command('flush', interactive=False)

    def _execute(self):
        management.call_command('generaterealdata')

    def _get_post_execute_info(self):
        info = {}
        info['ExerciseLog.objects.count'] = ExerciseLog.objects.count()
        info['VideoLog.objects.count'] = VideoLog.objects.count()
        info['UserLog.objects.count'] = UserLog.objects.count()
        info['Facility.objects.count'] = Facility.objects.count()
        info['FacilityUser.objects.count'] = FacilityUser.objects.count()
        info['FacilityGroup.objects.count'] = FacilityGroup.objects.count()
        return info


class OneThousandRandomReads(base.Common):
    """
    One thousand random accesses of the video and exercise logs (500 of each)
    The IO in the test is primarily SELECT and will normally be cached in memory
    """

    def _setup(self, **kwargs):
        super(OneThousandRandomReads, self)._setup(**kwargs)

        # Give the platform a chance to cache the logs
        self.exercise_list = ExerciseLog.objects.get_query_set()
        self.video_list = VideoLog.objects.get_query_set()
        self.exercise_count = ExerciseLog.objects.count()
        self.video_count = VideoLog.objects.count()

    def _execute(self):
        for x in range(500):
            VideoLog.objects.get(id=self.video_list[int(self.random.random()*self.video_count)].id)
            ExerciseLog.objects.get(id=self.exercise_list[int(self.random.random()*self.exercise_count)].id)

    def _get_post_execute_info(self):
        return {"total_records_accessed": 1000}


class OneHundredRandomLogUpdates(base.UserCommon):
    """
    One hundred random accesses and updates tothe video and exercise logs (50 of each)
    The I/O here is SELECT and UPDATE - update will normally generate physical media access
    """
    def _setup(self, num_logs=50, **kwargs):
        super(OneHundredRandomLogUpdates, self)._setup(**kwargs)
        node_cache = get_node_cache()

        try:
            self.user = FacilityUser.objects.get(username=self.username)
        except:
            #take username from ExerciseLog
            all_exercises = ExerciseLog.objects.all()
            self.user = FacilityUser.objects.get(id=all_exercises[0].user_id)
            print self.username, " not in FacilityUsers, using ", self.user
        self.num_logs = num_logs
        #give the platform a chance to cache the logs
        ExerciseLog.objects.filter(user=self.user).delete()
        for x in range(num_logs):
            while True:
                ex_idx = int(self.random.random() * len(node_cache["Exercise"].keys()))
                ex_id = node_cache["Exercise"].keys()[ex_idx]
                if not ExerciseLog.objects.filter(user=self.user, exercise_id=ex_id):
                    break
            ex = ExerciseLog(user=self.user, exercise_id=ex_id)
            ex.save()
        self.exercise_list = ExerciseLog.objects.filter(user=self.user)
        self.exercise_count = self.exercise_list.count()

        VideoLog.objects.filter(user=self.user).delete()
        for x in range(num_logs):
            while True:
                vid_idx = int(self.random.random() * len(node_cache["Content"].keys()))
                vid_id = node_cache["Content"].keys()[vid_idx]
                if not VideoLog.objects.filter(user=self.user, video_id=vid_id):
                    break
            vid = VideoLog(user=self.user, video_id=vid_id)
            vid.save()
        self.video_list = VideoLog.objects.filter(user=self.user)
        self.video_count = self.video_list.count()


    def _execute(self):
        for x in range(50):
            this_video = VideoLog.objects.get(id=self.video_list[int(self.random.random()*self.video_count)].id)
            this_video.save()
            this_exercise = ExerciseLog.objects.get(id=self.exercise_list[int(self.random.random()*self.exercise_count)].id)
            this_exercise.save()

    def _get_post_execute_info(self):
        return {"total_records_updated": 100}


class OneHundredRandomLogUpdatesSingleTransaction(OneHundredRandomLogUpdates):
    """
    Same as above, but this time, only commit transactions at the end of the _execute phase.
    """
    @transaction.commit_on_success
    def _execute(self):
        super(OneHundredRandomLogUpdatesSingleTransaction, self)._execute()


class LoginLogout(base.SeleniumCommon):

    def _setup(self, **kwargs):
        kwargs["timeout"] = kwargs.get("timeout", 30)
        super(LoginLogout, self)._setup(**kwargs)

        # Store all
        self.max_wait_time = 5.
        self.browser.get(self.url)

        # Go to the expected page
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.title_contains(("Home")))
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "nav_login")))

        wait_to_start_time = self.random.random() * self.max_wait_time
        print "Waiting for %fs before starting." % wait_to_start_time
        time.sleep(wait_to_start_time)
        print "Go!"

    def _execute(self):
        elem = self.browser.find_element_by_id("nav_login")
        elem.send_keys(Keys.RETURN)

        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.title_contains(("Log in")))
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "id_username")))
        elem = self.browser.find_element_by_id("id_username")
        elem.send_keys(self.username)
        elem = self.browser.find_element_by_id("id_password")
        elem.send_keys(self.password + Keys.RETURN)

    def _get_post_execute_info(self):
        try:
            # logout
            wait = ui.WebDriverWait(self.browser, self.timeout)
            wait.until(expected_conditions.element_to_be_clickable((By.ID, "nav_logout")))
            elem = self.browser.find_element_by_id("nav_logout")
            elem.send_keys(Keys.RETURN)

            # verify
            wait = ui.WebDriverWait(self.browser, self.timeout)
            wait.until(expected_conditions.visibility_of_element_located(["id", "logged-in-name"]))
            wait = ui.WebDriverWait(self.browser, self.timeout)
            wait.until(expected_conditions.element_to_be_clickable((By.ID, "nav_login")))
        finally:
            info = {}
            info["url"] = self.url
            info["username"] = self.username

        return info


class SeleniumStudent(base.SeleniumCommon):

    """student username/password will be passed in
        behaviour of this student will be determined by
        seed value - seeds will typically be between 1 and 40 representing
        each student in the class, but actually it is not important
        starttime is the django (Chicago) time!!!!  Using start time allows us to cue-up a bunch of students
         and then release them into the wild.
        behaviour profile is a seed to decide which activities the student will carry out.
          Students with the same profile will follow the same behaviour.

    """
    def _setup(self, starttime="00:00", duration=30, **kwargs):
        kwargs["timeout"] = kwargs.get("timeout", 240)
        super(SeleniumStudent, self)._setup(**kwargs)

        self.return_list = []
        self.duration = duration
        self.host_url = self.url  # assume no trailing slash
        self.exercise_count = 0
        self.activity = self._setup_activities()

        def wait_until_starttime(starttime):
            time_to_sleep = (self.random.random() * 10.0) + 10
            if self.verbosity >= 1:
                print("(" + str(self.behavior_profile-24601) + ") waiting until it's time to start (%.1fs)." % time_to_sleep)
            time.sleep(time_to_sleep) #sleep
            now = datetime.datetime.today()
            if now.hour >= int(starttime[:2]):
                if now.minute >= int(starttime[-2:]):
                    return False
            logging.debug("Go!")
            return True
        while wait_until_starttime(starttime):
            pass #wait until lesson starttime

    def _setup_activities(self):
        """
        # self.activity simulates the classroom activity for the student
        # All students begin with activity "begin".
        # A random 2dp number <= 1.0 is then generated, and the next step is decided, working
        #  left to right through the list.
        # This allows a pseudo-random system usage - the behavior_profile seeds the random
        #  number generator, so identical behaviour profiles will follow the same route through
        #  the self.activity sequence.
        #
        # we are hard-coded here for the following videos, so they need to be downloaded before beginning:
        #  o Introduction to carrying when adding
        #  o Example: Adding two digit numbers (no carrying)
        #  o Subtraction 2
        #  o Example: 2-digit subtraction (no borrowing)
        #  o Level 2 Addition
        """

        self.activity = {}

        self.activity["begin"]= {  # wait
                "method":self._pass, "duration": 1+(self.random.random()*3),
                "args":{},
                "nextstep":[(1.00, "begin_2")]
                 }

        self.activity["begin_2"]= {  # go to the homepage
                "method":self._get_path, "duration":1+(self.random.random()*3),
                "args":{"path":""},
                "nextstep":[(1.00, "begin_3")]
                }
        self.activity["begin_3"]= {  # click the login link
                "method":self._click, "duration":2+(self.random.random()*3),
                "args":{"find_by":By.ID, "find_text":"nav_login"},
                "nextstep":[(1.00, "login")]
                 }

        self.activity["login"]= {  # enter login info
                "method":self._do_login_step_1, "duration": 3,
                "args":{"username":self.username, "password": self.password},
                "nextstep":[(1.00, "login_2")]
                 }
        self.activity["login_2"]= {  # do nothing, just choose whereto go next
                "method":self._do_login_step_2, "duration": 3,
                "args":{},
                "nextstep":[(1.00, "decide")]
                 }
        self.activity["decide"]= {
                "method":self._pass, "duration": 2+ self.random.random() * 3,
                "args":{},
                "nextstep":[(.10, "decide"), (.25, "watch"), (.98, "exercise"), (1.00, "end")]
                 }

        self.activity["watch"]= {
                "method":self._pass, "duration":1,
                "args":{},
                "nextstep":[(.95, "w1"),(1.00, "exercise")]
                 }
        self.activity["w1"]= {
                "method":self._get_path, "duration":4,
                "args":{"path":"/math/"},
                "nextstep":[(1.00, "w2")]
                 }
        self.activity["w2"]= {
                "method":self._get_path, "duration":3+(self.random.random()*5),
                "args":{"path":"/math/arithmetic/"},
                "nextstep":[(1.00, "w3")]
                }
        self.activity["w3"]= {
                "method":self._get_path, "duration":2+(self.random.random()*12),
                "args":{"path":"/math/arithmetic/addition-subtraction/"},
                "nextstep":[(1.00, "w4")]
                 }
        self.activity["w4"]= {
                "method":self._get_path, "duration":6,
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/"},
                "nextstep":[(1.00, "w5")]
                 }
        self.activity["w5"]= {
                "method":self._get_path, "duration":2,
                "args":{"path":"/math/arithmetic/"},
                "nextstep":[(.20, "wv1"), (.40, "wv2"), (.60, "wv3"), (.80, "wv4"), (1.00, "wv5")]
            }

        self.activity["wv1"]= {
                "method":self._get_path, "duration":4+(self.random.random()*7),
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/v/addition-2/"},
                "nextstep":[(1.00, "wv1_1")]
                 }
        self.activity["wv1_1"]= {
                "method":self._do_vid, "duration":750,
                "args":{},
                "nextstep":[(.10, "wv1_1"), (.20, "wv2"), (1.00, "decide")]
                 }

        self.activity["wv2"]= {
                "method":self._get_path, "duration":3,
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/v/adding-whole-numbers-and-applications-1/"},
                "nextstep":[(1.00, "wv2_1")]
                 }
        self.activity["wv2_1"]= {
                "method":self._do_vid, "duration":95,
                "args":{},
                "nextstep":[(.10, "wv2_1"), (.70, "eadd2"), (1.00, "decide")]
                 }

        self.activity["wv3"]= {
                "method":self._get_path, "duration":5,
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/v/subtraction-2/"},
                "nextstep":[(1.00, "wv3_1")]
                 }
        self.activity["wv3_1"]= {
                "method":self._do_vid, "duration":760,
                "args":{},
                "nextstep":[(.10, "wv3_1"), (.30, "wv4"), (.90, "esub2"), (1.00, "decide")]
                 }

        self.activity["wv4"]= {
                "method":self._get_path, "duration":3,
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/v/subtracting-whole-numbers/"},
                "nextstep":[(1.00, "wv4_1")]
                 }
        self.activity["wv4_1"]= {
                "method":self._do_vid, "duration":175,
                "args":{},
                "nextstep":[(.10, "wv4_1"), (.30, "wv5"), (.90, "esub2"), (1.00, "decide")]
                 }

        self.activity["wv5"]= {
                "method":self._get_path, "duration":3,
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/v/level-2-addition/"},
                "nextstep":[(1.00, "wv5_1")]
                 }
        self.activity["wv5_1"]= {
                "method":self._do_vid, "duration":580,
                "args":{},
                "nextstep":[(.10, "wv5_1"), (.70, "eadd2"), (.80, "decide")]
                 }

        self.activity["exercise"]= {
                "method":self._pass, "duration":1,
                "args":{},
                "nextstep":[(.60, "eadd2"),(1.00, "esub2")]
                 }
        self.activity["eadd2"]= {
                "method":self._click, "duration":4+(self.random.random()*3),
                "args":{"find_by":By.ID, "find_text":"nav_practice"},
                "nextstep":[(1.00, "neadd2_1")]
                 }
        self.activity["neadd2"]= {
                "method":self._get_path, "duration":5,
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/e/addition_2/"},
                "nextstep":[(1.00, "weadd2")]
                 }
        self.activity["weadd2"]= {
                "method":self._wait_for_element, "duration":5,
                "args":{"find_by":By.CSS_SELECTOR, "find_text":"#solutionarea input[type=text]"},
                "nextstep":[(1.00, "do_eadd2")]
                 }
        self.activity["do_eadd2"]= {
                "method":self._do_exer, "duration":3+(self.random.random()*9),
                "args":{},
                "nextstep":[(.03, "decide"), (.75, "do_eadd2"), (1.00, "esub2")]
                 }

        self.activity["esub2"]= {
                "method":self._click, "duration":3,
                "args":{"find_by":By.ID, "find_text":"nav_practice"},
                "nextstep":[(1.00, "nesub2_1")]
                 }
        self.activity["nesub2"]= {
                "method":self._get_path, "duration":3+(self.random.random()*3),
                "args":{"path":"/math/arithmetic/addition-subtraction/two_dig_add_sub/e/subtraction_2/"},
                "nextstep":[(1.00, "wesub2")]
                 }
        self.activity["wesub2"]= {
                "method":self._wait_for_element, "duration":6,
                "args":{"find_by":By.CSS_SELECTOR, "find_text":"#solutionarea input[type=text]"},
                "nextstep":[(1.00, "do_esub2")]
                 }
        self.activity["do_esub2"]= {
                "method":self._do_exer, "duration":9+(self.random.random()*7),
                "args":{},
                "nextstep":[(.03, "decide"), (.75, "do_esub2"), (.91, "watch"), (1.00, "eadd2")]
                 }

        self.activity["end"] = {
                "method":self._do_logout, "duration":1,
                "args":{},
                "nextstep":[(1.00, "end")]
                 }
        return self.activity

    def _execute(self):
        current_activity = "begin"
        endtime = time.time() + (self.duration * 60.)

        while True:
            if time.time() >= endtime:
                current_activity = "end"

            # Prep and do the current activity
            try:
                start_clock_time = datetime.datetime.today()
                start_time = time.time()
                result=self.activity[current_activity]["method"](self.activity[current_activity]["args"])
                self.return_list.append((
                        current_activity,
                        '%02d:%02d:%02d' % (start_clock_time.hour,start_clock_time.minute,start_clock_time.second),
                        round((time.time() - start_time),2),
                                        ))
            except Exception as e:
                if current_activity != "end":
                    raise
                else:
                    logging.error("Error on end: %s" % e)

            if current_activity == "end":
                break

            # Wait before the next activity
            if "duration" in self.activity[current_activity]:
                if self.verbosity >= 2:
                    print "(" + str(self.behavior_profile-24601) + ")" + "sleeping for ", self.activity[current_activity]["duration"]
                time.sleep(self.activity[current_activity]["duration"])

            # Choose the next activity
            next_activity_random = round(self.random.random(),2)
            for threshold, next_activity in self.activity[current_activity]["nextstep"]:
                if threshold >= next_activity_random:
                    if self.verbosity >= 2:
                        print "(" + str(self.behavior_profile-24601) + ")" + str(next_activity_random), "next_activity =", next_activity
                    current_activity = next_activity
                    break

    def _pass(self, args):
        pass

    def _click(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((args["find_by"], args["find_text"])))
        if args["find_by"] == By.ID:
            elem = self.browser.find_element_by_id(args["find_text"])
        elif args["find_by"] == By.PARTIAL_LINK_TEXT:
            elem = self.browser.find_element_by_partial_link_text(args["find_text"])
        elem.send_keys(Keys.RETURN)

    def _wait_for_element(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((args["find_by"], args["find_text"])))

    def _do_exer(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, '#solutionarea input[type=text]')))
        elem = self.browser.find_element_by_css_selector('#solutionarea input[type=text]')
        elem.click()
        elem.clear()
        elem.send_keys(int(self.random.random()*11111.)) # a wrong answer, but we don't care
        self.exercise_count += 1
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "check-answer-button")))
        elem = self.browser.find_element_by_id("check-answer-button")
        elem.send_keys(Keys.RETURN)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, '#solutionarea input[type=text]')))

    def _do_vid(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "div#video-element.video-js div.vjs-big-play-button")))
        elem = self.browser.find_element_by_css_selector("div#video-element.video-js div.vjs-big-play-button")
        elem.click()

    def _do_login_step_1(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.title_contains(("Log in")))
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "id_username")))
        elem = self.browser.find_element_by_id("id_username")
        elem.send_keys(args["username"])
        elem = self.browser.find_element_by_id("id_password")
        elem.send_keys(args["password"])
        elem.send_keys(Keys.RETURN)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.visibility_of_element_located(["id", "logged-in-name"]))

    def _do_login_step_2(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "nav_logout")))

    def _do_logout(self, args):
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "nav_logout")))
        elem = self.browser.find_element_by_id("nav_logout")
        elem.send_keys(Keys.RETURN)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "nav_login")))

    def _get_path(self, args):
        assert args.get("path") is not None, "args['path'] must not be None"
        path = self.host_url
        if not args["path"] or args["path"][0] != "/":
            path += "/"
        path += args["path"]

        self.browser.get(path)

    def _get_post_execute_info(self):
        #we are done! class over, lets get out of here
        return {"timings":self.return_list, "behavior_profile":self.behavior_profile}

    def _teardown(self):
        if self.verbosity >= 1:
            print "(" + self.username + ") exercises completed = " + str(self.exercise_count)
        self.browser.close()


class SeleniumStudentExercisesOnly(SeleniumStudent):
    def _setup(self, *args, **kwargs):
        super(SeleniumStudentExercisesOnly, self)._setup(*args, **kwargs)
        self.activity["decide"]["nextstep"] = [(.10, "decide"), (1.00, "exercise")]
        self.activity["do_esub2"]["nextstep"] =[(.03, "decide"), (.75, "do_esub2"), (1.00, "eadd2")]
