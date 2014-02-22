"""
# Data design:
#
# We want:
#   * more data (over a larger set of topics, showing progression/mastery?)
#   * user data generated from underlying variables:
#     - speed_of_learning (0 to 1, mean 0.5)
#     - effort_level (0 to 1, mean 0.5)
#     - time_in_program (determines # of samples)
#   * four types of users:
#     - normal       (60%)
#     - unchallenged (13%): high speed_of_learning, low effort_level
#     - struggling   (13%): low speed_of_learning, high effort_level
#     - inactive     (13%): no learning whatsoever
#
#
# TODO(bcipolli):
# The parameters for the fake users are saved, and reused if the same user is randomly
#   "regenerated here.
# Perhaps worth having the ability to target only particular existing users to further
#   generate data?
"""
import datetime
import random
import re
import json
from math import exp, sqrt, ceil, floor
from optparse import make_option

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import settings
import securesync
from facility.models import Facility, FacilityUser, FacilityGroup
from main.models import ExerciseLog, VideoLog, UserLog
from main.topic_tools import get_topic_videos, get_topic_exercises
from securesync.models import Device, DeviceMetadata
from settings import LOG as logging
from utils.general import datediff


firstnames = ["Vuzy", "Liz", "Ben", "Richard", "Kwame", "Jamie", "Alison", "Nadia", "Zenab", "Guan", "Dylan", "Vicky",
              "Melanie", "Michelle", "Yamira", "Elena", "Thomas", "Jorge", "Lucille", "Arnold", "Rachel", "Daphne", "Sofia"]

lastnames = ["Awolowo", "Clement", "Smith", "Ramirez", "Hussein", "Wong", "St. Love", "Franklin", "Lopez", "Brown", "Paterson",
             "De Soto", "Khan", "Mench", "Merkel", "Roschenko", "Picard", "Jones", "French", "Karnowski", "Boyle", "Burke", "Tan"]

# We want to show some users that have a correlation between effort and mastery, some that show mastery without too much effort (unchallenged), and some that show little mastery with a lot of effort
# Each 4-uple represents: (mean,std of gaussian, min/max values)
user_types = [
    {"name": "common",       "weight": 0.6, "speed_of_learning": (0.5, 0.5,  0.05, 0.95), "effort_level": (0.5,  0.5,  0.05, 0.95), "time_in_program": (0.5, 0.5, 0.05, 0.95)},
    {"name": "unchallenged", "speed_of_learning": (0.75, 0.25, 0.05, 0.95), "effort_level": (0.25, 0.25, 0.05, 0.95), "time_in_program": (0.5, 0.5, 0.05, 0.95)},
    {"name": "struggling",   "speed_of_learning": (0.25, 0.25, 0.05, 0.95), "effort_level": (0.75, 0.25, 0.05, 0.95), "time_in_program": (0.5, 0.5, 0.05, 0.95)},
    {"name": "inactive",     "speed_of_learning": (0.25, 0.25, 0.05, 0.95), "effort_level": (0.0,  0.0,  0.00, 0.00), "time_in_program": (0.5, 0.5, 0.05, 0.95)},
]


def select_all_exercises(topic_name):
    # This function needs to traverse all children (recursively?) to select out all exercises.
    # Note: this function may exist
    pass

topics = ["arithmetic"]


def generate_user_type(n=1):
    n_types = len(user_types)
    common_weight = user_types[0]["weight"]
    other_weight = (1. - common_weight) / (n_types - 1)
    # 0: 60%=common, 1: 20%=unchallenged; 2: 20%=struggling
    return [int(ceil(random.random() / other_weight - (common_weight / other_weight))) for ni in range(n)]


def sample_user_settings():
    user_type = user_types[generate_user_type()[0]]
    user_settings = {
        "name": user_type["name"],
        "speed_of_learning": max(user_type["speed_of_learning"][2], min(user_type["speed_of_learning"][3], random.gauss(user_type["speed_of_learning"][0], user_type["speed_of_learning"][1]))),
        "effort_level":      max(user_type["effort_level"][2],      min(user_type["effort_level"][3],      random.gauss(user_type["effort_level"][0],      user_type["effort_level"][1]))),
        "time_in_program":   max(user_type["time_in_program"][2],   min(user_type["time_in_program"][3],   random.random()))  # (user_type["time_in_program"][0],   user_type["time_in_program"][1]),
    }
    return user_settings


def username_from_name(first_name, last_name):
    return re.sub(r"[\s\.]", "_", (first_name[0] + last_name).lower())


def sigmoid(theta, a, b):
    return 1.0 / (1.0 + exp(b - a * theta))


def generate_fake_facilities(names=("Wilson Elementary",)):
    """Add the given fake facilities"""
    facilities = []

    for name in names:
        found_facilities = Facility.objects.filter(name=name)
        if found_facilities:
            facility = found_facilities[0]
            logging.info("Retrieved facility '%s'" % name)
        else:
            facility = Facility(name=name)
            facility.save()
            logging.info("Created facility '%s'" % name)

        facilities.append(facility)

    return facilities


def generate_fake_facility_groups(names=("Class 4E", "Class 5B"), facilities=None):
    """Add the given fake facility groups to the given fake facilities"""

    if not facilities:
        facilities = generate_fake_facilities()

    facility_groups = []
    for facility in facilities:
        for name in names:
            found_facility_groups = FacilityGroup.objects.filter(facility=facility, name=name)
            if found_facility_groups:
                facility_group = found_facility_groups[0]
                logging.info("Retrieved facility group '%s'" % name)
            else:
                facility_group = FacilityGroup(facility=facility, name=name)
                facility_group.save()
                logging.info("Created facility group '%s'" % name)

            facility_groups.append(facility_group)

    return (facility_groups, facilities)


def generate_fake_facility_users(nusers=20, facilities=None, facility_groups=None, password="hellothere"):
    """Add the given fake facility users to each of the given fake facilities.
    If no facilities are given, they are created."""

    if not facility_groups:
        (facility_groups, facilities) = generate_fake_facility_groups(facilities=facilities)

    facility_users = []

    cur_usernum = 0
    users_per_group = nusers / len(facility_groups)

    for facility in facilities:
        for facility_group in facility_groups:
            for i in range(0, users_per_group):
                user_data = {
                    "first_name": random.choice(firstnames),
                    "last_name":  random.choice(lastnames),
                }
                user_data["username"] = username_from_name(user_data["first_name"], user_data["last_name"])

                try:
                    facility_user = FacilityUser.objects.get(facility=facility, username=user_data["username"])
                    facility_user.group = facility_group
                    facility_user.save()
                    logging.info("Retrieved facility user '%s/%s'" % (facility.name, user_data["username"]))
                except FacilityUser.DoesNotExist as e:
                    notes = json.dumps(sample_user_settings())

                    facility_user = FacilityUser(
                        facility=facility,
                        username=user_data["username"],
                        first_name=user_data["first_name"],
                        last_name=user_data["last_name"],
                        notes=notes,
                        group=facility_group,
                    )
                    facility_user.set_password(password)  # set same password for every user
                    facility_user.save()
                    logging.info("Created facility user '%s/%s'" % (facility.name, user_data["username"]))

                facility_users.append(facility_user)

                cur_usernum += 1  # this is messy and could be done more intelligently;
                                 # could also randomize to add more users, as this function
                                 # seems to be generic, but really is not.

    return (facility_users, facility_groups, facilities)


def probability_of(qty, user_settings):
    """Share some probabilities across exercise and video logs"""
    if qty in ["exercise", "video"]:
        return sqrt(user_settings["effort_level"] * 3 * user_settings["time_in_program"])
    if qty == "completed":
        return (0.33 * user_settings["effort_level"] + 0.66 * user_settings["speed_of_learning"]) * 2 * user_settings["time_in_program"]
    if qty == "attempts":
        return (0.33 * user_settings["effort_level"] + 0.55 * user_settings["time_in_program"]) / probability_of("completed", user_settings) / 5


def generate_fake_exercise_logs(facility_user=None, topics=topics, start_date=datetime.datetime.now() - datetime.timedelta(days=30 * 6)):
    """Add exercise logs for the given topics, for each of the given users.
    If no users are given, they are created.
    If no topics exist, they are taken from the list at the top of this file.

    By default, users start learning randomly between 6 months ago and now.
    """

    own_device = Device.get_own_device()
    date_diff = datetime.datetime.now() - start_date
    exercise_logs = []
    user_logs = []

    # It's not a user: probably a list.
    # Recursive case
    if not hasattr(facility_user, "username"):
        # It's NONE :-/ generate the users first!
        if not facility_user:
            (facility_user, _, _) = generate_fake_facility_users()

        for topic in topics:
            for user in facility_user:
                (elogs, ulogs) = generate_fake_exercise_logs(facility_user=user, topics=[topic], start_date=start_date)
                exercise_logs.append(elogs)
                user_logs.append(ulogs)

    # Actually generate!
    else:
        # Get (or create) user type
        try:
            user_settings = json.loads(facility_user.notes)
        except:
            user_settings = sample_user_settings()
            facility_user.notes = json.dumps(user_settings)
            facility_user.save()
        date_diff_started = datetime.timedelta(seconds=datediff(date_diff, units="seconds") * user_settings["time_in_program"])  # when this user started in the program, relative to NOW

        for topic in topics:
            # Get all exercises related to the topic
            exercises = get_topic_exercises(topic_id=topic)

            # Problem:
            #   Not realistic for students to have lots of unfinished exercises.
            #   If they start them, they tend to get stuck, right?
            #
            # So, need to make it more probable that they will finish an exercise,
            #   and less probable that they start one.
            #
            # What we need is P(streak|started), not P(streak)

            # Probability of doing any particular exercise
            p_exercise = probability_of(qty="exercise", user_settings=user_settings)
            logging.debug("# exercises: %d; p(exercise)=%4.3f, user settings: %s\n" % (len(exercises), p_exercise, json.dumps(user_settings)))

            # of exercises is related to
            for j, exercise in enumerate(exercises):
                if random.random() > p_exercise:
                    continue

                # Probability of completing this exercise, and .. proportion of attempts
                p_completed = probability_of(qty="completed", user_settings=user_settings)
                p_attempts = probability_of(qty="attempts", user_settings=user_settings)

                attempts = int(random.random() * p_attempts * 30 + 10)  # always enough to have completed
                completed = (random.random() < p_completed)
                if completed:
                    streak_progress = 100
                else:
                    streak_progress = max(0, min(90, random.gauss(100 * user_settings["speed_of_learning"], 20)))
                    streak_progress = int(floor(streak_progress / 10.)) * 10
                points = streak_progress / 10 * 12 if completed else 0  # only get points when you master.

                # Choose a rate of exercises, based on their effort level and speed of learning.
                #   Compute the latest possible start time.
                #   Then sample a start time between their start time
                #   and the latest possible start_time
                rate_of_exercises = 0.66 * user_settings["effort_level"] + 0.33 * user_settings["speed_of_learning"]  # exercises per day
                time_for_attempts = min(datetime.timedelta(days=rate_of_exercises * attempts), date_diff_started)  # protect with min
                time_delta_completed = datetime.timedelta(seconds=random.randint(int(datediff(time_for_attempts, units="seconds")), int(datediff(date_diff_started, units="seconds"))))
                date_completed = datetime.datetime.now() - time_delta_completed

                # Always create new
                logging.info("Creating exercise log: %-12s: %-25s (%d points, %d attempts, %d%% streak on %s)" % (
                    facility_user.first_name,
                    exercise["name"],
                    points,
                    attempts,
                    streak_progress,
                    date_completed,
                ))
                try:
                    elog = ExerciseLog.objects.get(user=facility_user, exercise_id=exercise["name"])
                except ExerciseLog.DoesNotExist:
                    elog = ExerciseLog(
                        user=facility_user,
                        exercise_id=exercise["name"],
                        attempts=int(attempts),
                        streak_progress=streak_progress,
                        points=int(points),
                        complete=completed,
                        completion_timestamp=date_completed,
                    )
                    elog.save(update_userlog=False)

                    # For now, make all attempts on an exercise into a single UserLog.
                    seconds_per_attempt = 10 * (1 + user_settings["speed_of_learning"] * random.random())
                    time_to_navigate = 15 * (0.5 + random.random())  #between 7.5s and 22.5s
                    time_to_logout = 5 * (0.5 + random.random()) # between 2.5 and 7.5s
                    if UserLog.is_enabled():
                        ulog = UserLog(
                            user=facility_user,
                            activity_type=1,
                            start_datetime = date_completed - datetime.timedelta(seconds=int(attempts * seconds_per_attempt + time_to_navigate)),
                            end_datetime = date_completed + datetime.timedelta(seconds=time_to_logout),
                            last_active_datetime = date_completed,
                        )
                        ulog.save()
                        user_logs.append(ulog)
                exercise_logs.append(elog)

    return (exercise_logs, user_logs)


def generate_fake_video_logs(facility_user=None, topics=topics, start_date=datetime.datetime.now() - datetime.timedelta(days=30 * 6)):
    """Add video logs for the given topics, for each of the given users.
    If no users are given, they are created.
    If no topics exist, they are taken from the list at the top of this file."""

    own_device = Device.get_own_device()
    date_diff = datetime.datetime.now() - start_date
    video_logs = []

    # It's not a user: probably a list.
    # Recursive case
    if not hasattr(facility_user, "username"):
        # It's NONE :-/ generate the users first!
        if not facility_user:
            (facility_user, _, _) = generate_fake_facility_users()

        for topic in topics:
            for user in facility_user:
                video_logs.append(generate_fake_video_logs(facility_user=user, topics=[topic], start_date=start_date))

    # Actually generate!
    else:
        # First, make videos for the associated logs

        # Then make some unassociated videos, to simulate both exploration
        #   and watching videos without finishing.
        # Get (or create) user type
        try:
            user_settings = json.loads(facility_user.notes)
        except:
            user_settings = sample_user_settings()
            facility_user.notes = json.dumps(user_settings)
            facility_user.save()

        date_diff_started = datetime.timedelta(seconds=datediff(date_diff, units="seconds") * user_settings["time_in_program"])  # when this user started in the program, relative to NOW

        for topic in topics:
            videos = get_topic_videos(topic_id=topic)

            exercises = get_topic_exercises(topic_id=topic)
            exercise_ids = [ex["id"] if "id" in ex else ex['name'] for ex in exercises]
            exercise_logs = ExerciseLog.objects.filter(user=facility_user, id__in=exercise_ids)

            # Probability of watching a video, irrespective of the context
            p_video_outer = probability_of("video", user_settings=user_settings)
            logging.debug("# videos: %d; p(videos)=%4.3f, user settings: %s\n" % (len(videos), p_video_outer, json.dumps(user_settings)))

            for video in videos:
                p_completed = probability_of("completed", user_settings=user_settings)

                # If we're just doing random videos, fine.
                # If these videos relate to exercises, then suppress non-exercise-related videos
                #   for this user.
                p_video = p_video_outer  # start with the context-free value
                did_exercise = False
                if exercise_logs.count() > 0:
                    # 5x less likely to watch a video if you haven't done the exercise,
                    if "related_exercise" not in video:
                        p_video /= 5  # suppress

                    # 5x more likely to watch a video if they've done the exercise
                    # 2x more likely to have finished it.
                    else:
                        exercise_log = ExerciseLog.objects.filter(user=facility_user, id=video["related_exercise"]["id"])
                        did_exercise = exercise_log.count() != 0
                        if did_exercise:
                            p_video *= 5
                            p_completed *= 2

                # Do the sampling
                if p_video < random.random():
                    continue
                    # didn't watch it
                elif p_completed > random.random():
                    pct_completed = 100.
                else:      # Slower students will use videos more.  Effort also important.
                    pct_completed = 100. * min(1., sqrt(random.random() * sqrt(user_settings["effort_level"] * user_settings["time_in_program"] / sqrt(user_settings["speed_of_learning"]))))
                # Compute quantities based on sample
                total_seconds_watched = int(video["duration"] * pct_completed / 100.)
                points = int(750 * pct_completed / 100.)

                # Choose a rate of videos, based on their effort level.
                #   Compute the latest possible start time.
                #   Then sample a start time between their start time
                #   and the latest possible start_time
                if did_exercise:
                    # More jitter if you learn fast, less jitter if you try harder (more diligent)
                    date_jitter = datetime.timedelta(days=max(0, random.gauss(1, user_settings["speed_of_learning"] / user_settings["effort_level"])))
                    date_completed = exercise_log[0].completion_timestamp - date_jitter
                else:
                    rate_of_videos = 0.66 * user_settings["effort_level"] + 0.33 * user_settings["speed_of_learning"]  # exercises per day
                    time_for_watching = total_seconds_watched
                    time_delta_completed = datetime.timedelta(seconds=random.randint(int(time_for_watching), int(datediff(date_diff_started, units="seconds"))))
                    date_completed = datetime.datetime.now() - time_delta_completed

                try:
                    vlog = VideoLog.objects.get(user=facility_user, video_id=video["id"])
                except VideoLog.DoesNotExist:

                    logging.info("Creating video log: %-12s: %-45s (%4.1f%% watched, %d points)%s" % (
                        facility_user.first_name,
                        video["title"],
                        pct_completed,
                        points,
                        " COMPLETE on %s!" % date_completed if pct_completed == 100 else "",
                    ))
                    vlog = VideoLog(
                        user=facility_user,
                        video_id=video["id"],
                        youtube_id=video["youtube_id"],
                        total_seconds_watched=total_seconds_watched,
                        points=points,
                        complete=(pct_completed == 100.),
                        completion_timestamp=date_completed,
                    )
                    vlog.save(update_userlog=False)  # avoid userlog issues

                video_logs.append(vlog)

    return video_logs

def generate_fake_coachreport_logs(password="hellothere"):
    t,_ = FacilityUser.objects.get_or_create(
        facility=Facility.objects.all()[0],
        username=random.choice(firstnames)
    )
    t.set_password(password)

    # TODO: create flags later
    num_logs = 20
    logs = []
    for _ in xrange(num_logs):
        date_logged_in = datetime.datetime.now() - datetime.timedelta(days=random.randint(1,10))
        date_viewed_coachreport = date_logged_in + datetime.timedelta(minutes=random.randint(0, 30))
        date_logged_out = date_viewed_coachreport + datetime.timedelta(minutes=random.randint(0, 30))
        login_log = UserLog.objects.create(
            user=t,
            activity_type=UserLog.get_activity_int("login"),
            start_datetime=date_logged_in,
            last_active_datetime=date_viewed_coachreport,
            end_datetime=date_logged_out,
        )
        logging.info("created login log for teacher %s" % t.username)
        coachreport_log = UserLog.objects.create(
            user=t,
            activity_type=UserLog.get_activity_int("coachreport"),
            start_datetime=date_viewed_coachreport,
            last_active_datetime=date_viewed_coachreport,
            end_datetime=date_viewed_coachreport,
        )
        logs.append((login_log, coachreport_log))
        logging.info("created coachreport log for teacher %s" % t.username)
    return logs


class Command(BaseCommand):
    args = "<data_type=[facility,facility_users,facility_groups,default=exercises,videos]>"

    help = "Generate fake user data.  Can be re-run to generate extra exercise and video data."

    option_list = BaseCommand.option_list + (
        make_option('-t', '--transaction',
            action='store_true',
            dest='in_transaction',
            default=False,
            help='Create all objects in a single transaction',
            metavar="TRANSACTION"),
    )

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("Don't run this on the central server!!  Data not linked to any zone on the central server is BAD.")

        if options["in_transaction"]:
            with transaction.commit_on_success():
                self.handle_stuff(*args, **options)
        else:
            self.handle_stuff(*args, **options)


    def handle_stuff(self, *args, **options):
        # First arg is the type of data to generate
        generate_type = "all" if len(args) <= 0 else args[0].lower()

        if generate_type in ["facility", "facilities"]:
            generate_fake_facilities()

        elif generate_type in ["facility_groups"]:
            generate_fake_facility_groups()

        elif generate_type in ["facility_users"]:
            generate_fake_facility_users()  # default password

        elif generate_type in ["exercise", "exercises"]:
            (facility_users, _, _) = generate_fake_facility_users()  # default password
            generate_fake_exercise_logs(facility_user=facility_users)

        elif generate_type in ["video", "videos"]:
            (facility_users, _, _) = generate_fake_facility_users()  # default password
            generate_fake_video_logs(facility_user=facility_users)

        elif generate_type in ["coachreport, coachreports"]:
            generate_fake_coachreport_logs()

        elif generate_type in ["all"]:
            (facility_users, _, _) = generate_fake_facility_users()  # default password
            generate_fake_exercise_logs(facility_user=facility_users)
            generate_fake_video_logs(facility_user=facility_users)
            generate_fake_coachreport_logs()

        else:
            raise Exception("Unknown data type to generate: %s" % generate_type)
