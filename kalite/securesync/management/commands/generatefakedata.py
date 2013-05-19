from django.core.management.base import BaseCommand, CommandError
from securesync.models import Facility, FacilityUser, FacilityGroup, Device, DeviceMetadata
import securesync
from main.models import ExerciseLog, VideoLog
import random
import json
from math import exp, sqrt
from main import topicdata
import logging

import settings
from utils.topic_tools import get_videos_for_topic


firstnames = ["Richard","Kwame","Jamie","Alison","Nadia","Zenab","Guan","Dylan","Vicky","Melanie","Michelle","Yamira","Elena","Thomas","Jorge","Lucille","Arnold","Rachel","Daphne","Sofia"]

lastnames = ["Awolowo","Clement","Smith","Ramirez","Hussein","Wong","Franklin","Lopez","Brown","Paterson","De Soto","Khan","Mench","Merkel","Roschenko","Picard","Jones","French","Karnowski","Boyle"]

usernames = [firstname[0].lower() + lastname.lower() for firstname, lastname in zip(firstnames, lastnames)]

proficiency = [random.random() * 0.8 for i in range(10)] + [random.random() for i in range(10)]

topics = ["multiplication-division", "factors-multiples"]


def sigmoid(theta, a, b):
    return 1.0 / (1.0 + exp(b - a * theta))


def generate_fake_facilities(names=("Wilson Elementary",)):
    """Add the given fake facilities"""
    facilities = [];
    
    for name in names:
        try:
            facility = Facility.objects.get(name=name)
            logging.info("Retrieved facility '%s'" % name)
        except Facility.DoesNotExist as e:
            facility = Facility(name=name)
            facility.save()
            logging.info("Created facility '%s'" % name)
        
        facilities.append(facility)
        
    return facilities


def generate_fake_facility_groups(names=("Class 4E", "Class 5B"), facilities=None):
    """Add the given fake facility groups to the given fake facilities"""
    
    if not facilities:
        facilities = generate_fake_facilities()
        
    facility_groups = [];
    for facility in facilities:
        for name in names:
            try:
                facility_group = FacilityGroup.objects.get(facility=facility, name=name)
                logging.info("Retrieved facility group '%s'" % name)
            except FacilityGroup.DoesNotExist as e:
                facility_group = FacilityGroup(facility=facility, name=name)
                facility_group.full_clean()
                facility_group.save()
                logging.info("Created facility group '%s'" % name)
            
            facility_groups.append(facility_group)
        
    return (facility_groups,facilities)
        
        
def generate_fake_facility_users(usernames=usernames,firstnames=firstnames,lastnames=lastnames,facilities=None,facility_groups=None, password="blah"):
    """Add the given fake facility users to each of the given fake facilities.
    If no facilities are given, they are created."""

    if not facility_groups:
        (facility_groups,facilities) = generate_fake_facility_groups(facilities=facilities)
               
    facility_users = []
    
    cur_usernum = 0
    users_per_group = len(usernames)/len(facility_groups)
    
    for facility in facilities:
        for facility_group in facility_groups:
            for i in range(0,users_per_group):
                try:
                    facility_user = FacilityUser.objects.get(facility=facility, username=usernames[cur_usernum], first_name=firstnames[cur_usernum], last_name=lastnames[cur_usernum], group=facility_group)
                    logging.info("Retrieved facility user '%s/%s'" % (facility.name,usernames[cur_usernum]))
                except FacilityUser.DoesNotExist as e:
                    facility_user = FacilityUser(facility=facility, username=usernames[cur_usernum], first_name=firstnames[cur_usernum], last_name=lastnames[cur_usernum], group=facility_group)
                    facility_user.set_password(password) # set same password for every user
                    facility_user.full_clean()
                    facility_user.save()
                    logging.info("Created facility user '%s/%s'" % (facility.name,usernames[cur_usernum]))
                    
                facility_users.append(facility_user)
                cur_usernum += 1 # this is messy and could be done more intelligently; 
                                 # could also randomize to add more users, as this function
                                 # seems to be generic, but really is not.

    return (facility_users,facility_groups,facilities)
    

def generate_fake_exercise_logs(topics=topics,facility_users=None):
    """Add exercise logs for the given topics, for each of the given users.
    If no users are given, they are created.
    If no topics exist, they are taken from the list at the top of this file."""
    
    if not facility_users:
        (facility_users,_,_) = generate_fake_facility_users()
        
    exercise_logs = []
    
    for topic in topics:
        exercises = json.load(open("./static/data/topicdata/" + topic + ".json","r"))
        exercises = sorted(exercises, key = lambda k: (k["h_position"], k["v_position"]))
        
        # Determine proficiency
        exercises_a = [random.random() for i in range(len(exercises))]
        exercises_b = [float(i) / len(exercises) for i in range(len(exercises))]
        
        for i, user in enumerate(facility_users):
            for j, exercise in enumerate(exercises):
                sig = sigmoid(proficiency[i], exercises_a[j], exercises_b[j])
                if random.random() < 0.05 * (1-sig) and j > 2:
                    break
                if random.random() < 0.15:
                    continue
                    
                attempts = random.random() * 30 + 10
                streak_progress = max(10, 10*min(10, round(attempts * sqrt(random.random() * sig)))) # should be in increments of 10
                points   = attempts * 10 * sig
                
                # Always create new
                logging.info("Creating exercise log: %-12s: %-25s (%d points, %d attempts, %d%% streak)" % (user.first_name, exercise["name"],  int(points), int(attempts), int(streak_progress)))
                log = ExerciseLog(user=user, exercise_id=exercise["name"], attempts=int(attempts), streak_progress=int(streak_progress), points=int(points))
                log.full_clean()
                log.save()
                
                exercise_logs.append(log)

        return exercise_logs
        
        
def generate_fake_video_logs(topics=topics,facility_users=None):
    """Add video logs for the given topics, for each of the given users.
    If no users are given, they are created.
    If no topics exist, they are taken from the list at the top of this file."""
    
    if not facility_users:
        (facility_users,_,_) = generate_fake_facility_users()
        
    video_logs = []
    
    for topic in topics:
        videos = get_videos_for_topic(topic_id=topic)
        
        # Determine proficiency
        videos_a = [random.random() for i in range(len(videos))]
        videos_b = [float(i) / len(videos) for i in range(len(videos))]

        for i, user in enumerate(facility_users):
            for j, video in enumerate(videos):
                sig = sigmoid(proficiency[i], videos_a[j], videos_b[j])
                if random.random() > sig:
                    continue
                
                p_complete = sqrt(sqrt(sig))
                total_seconds_watched = video["duration"] if p_complete>=random.random() else video["duration"]*sqrt(random.random()*sig)
                points   = total_seconds_watched/10*10

                logging.info("Creating video log: %-12s: %-45s (%4.1f%% watched, %d points)%s" % (user.first_name, video["title"],  100*total_seconds_watched/video["duration"], int(points)," COMPLETE!" if int(total_seconds_watched)==video["duration"] else ""))
                log = VideoLog(user=user, youtube_id=video["youtube_id"], total_seconds_watched=int(total_seconds_watched), points=int(points))
                log.full_clean()
                log.save()
        
                video_logs.append(log)

        return video_logs
        
        
class Command(BaseCommand):
    args = "<data_type=[facility,facility_users,facility_groups,default=exercises,videos]>"

    help = "Generate fake user data.  Can be re-run to generate extra exercise and video data."

    def handle(self, *args, **options):
        logging.getLogger().setLevel(logging.INFO)
        
        # First arg is the type of data to generate
        generate_type = "exercises" if len(args)<=0 else args[0].lower()
                
        if "facility" == generate_type or "facilities" == generate_type: 
            generate_fake_facilities()
    
        elif "facility_groups" == generate_type: 
            generate_fake_facility_groups()
    
        elif "facility_users" == generate_type:
            generate_fake_facility_users() # default password
        
        elif "exercises" == generate_type:
            (facility_users,_,_) = generate_fake_facility_users() # default password
            generate_fake_exercise_logs(facility_users=facility_users)
            
        elif "videos" == generate_type:
            (facility_users,_,_) = generate_fake_facility_users() # default password
            generate_fake_video_logs(facility_users=facility_users)
            
        else:
            raise Exception("Unknown data type to generate: %s" % generate_type)

                