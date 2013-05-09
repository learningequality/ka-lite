import random
import json
import logging
import datetime
from math import exp, sqrt

from django.core.management.base import BaseCommand, CommandError

import settings
import securesync
from securesync.models import Facility, FacilityUser, FacilityGroup
from main.models import ExerciseLog, VideoLog, UserLog
from main import topicdata
from utils.topic_tools import get_videos_for_topic



def sigmoid(theta, a, b):
    return 1.0 / (1.0 + exp(b - a * theta))

firstnames = ["Richard","Kwame","Jamie","Alison","Nadia","Zenab","Guan","Dylan","Vicky","Melanie","Michelle","Yamira","Elena","Thomas","Jorge","Lucille","Arnold","Rachel","Daphne","Sofia"]

lastnames = ["Awolowo","Clement","Smith","Ramirez","Hussein","Wong","Franklin","Lopez","Brown","Paterson","De Soto","Khan","Mench","Merkel","Roschenko","Picard","Jones","French","Karnowski","Boyle"]

usernames = [firstname[0].lower() + lastname.lower() for firstname, lastname in zip(firstnames, lastnames)]

proficiency = [random.random() * 0.8 for i in range(10)] + [random.random() for i in range(10)]

topics = ["multiplication-division", "factors-multiples"]

class Command(BaseCommand):
    args = "<data_type=[Facility,FacilityUsers,FacilityGroups,default=Exercises,Videos]>"

    help = "Generate fake user data"

    def handle(self, *args, **options):
        logging.getLogger().setLevel(logging.INFO)
        
        generate_type = "exercises" if len(args)<=0 else args[0].lower()
            
        if "facility" == generate_type:
            Command.generateFakeFacilities()
        elif "facilityusers" == generate_type:
            Command.generateFakeFacilityUsers()
        elif "facilitygroups" == generate_type:
            Command.generateFakeFacilityGroups()
        else:
            (fu,_,_) = Command.generateFakeFacilityUsers()
            if "exercises" == generate_type:
                Command.generateFakeExerciseLogs(facilityusers=fu)
            elif "videos" == generate_type:
                Command.generateFakeVideoLogs(facilityusers=fu)
            else:
                raise Exception("Unknown data type to generate: %s"%generate_type)
                
                
    @staticmethod
    def generateFakeFacilities(names=("Wilson Elementary",)):
        """Add the given fake facilities"""
        facilities = [];
        for name in names:
            try:
                facilities.append(Facility.objects.get(name=name))
                logging.info("Retrieved facility '%s'"%name)
            except Facility.DoesNotExist as e:
                facilities.append(Facility(name=name))
                facilities[-1].save()
                logging.info("Created facility '%s'"%name)
            
        return facilities
    
    @staticmethod
    def generateFakeFacilityGroups(names=("Class 4E", "Class 5B"), facilities=None):
        """Add the given fake facility groups to the given fake facilities"""
        
        if not facilities:
            facilities = Command.generateFakeFacilities()
            
        groups = [];
        for facility in facilities:
            for name in names:
                try:
                    groups.append(FacilityGroup.objects.get(facility=facility, name=name))
                    logging.info("Retrieved facility group '%s'"%name)
                except FacilityGroup.DoesNotExist as e:
                    groups.append(FacilityGroup(facility=facility, name=name))
                    groups[-1].full_clean()
                    groups[-1].save()
                    logging.info("Created facility group '%s'"%name)
            
        return (groups,facilities)
            
       
    @staticmethod     
    def generateFakeFacilityUsers(usernames=usernames,firstnames=firstnames,lastnames=lastnames,facilities=None,groups=None):
    
        if not groups:
            (groups,facilities) = Command.generateFakeFacilityGroups(facilities=facilities)
                   
        facilityusers = []
        
        cur_usernum = 0
        users_per_group = len(usernames)/len(groups)
        
        for facility in facilities:
            for group in groups:
                for i in range(0,users_per_group):
                    try:
                        facilityusers.append(FacilityUser.objects.get(facility=facility, username=usernames[cur_usernum], first_name=firstnames[cur_usernum], last_name=lastnames[cur_usernum], group=group))
                        logging.info("Retrieved facility user '%s/%s'"%(facility.name,usernames[cur_usernum]))
                    except FacilityUser.DoesNotExist as e:
                        facilityusers.append(FacilityUser(facility=facility, username=usernames[cur_usernum], first_name=firstnames[cur_usernum], last_name=lastnames[cur_usernum], group=group))
                        facilityusers[-1].set_password("blah")
                        facilityusers[-1].full_clean()
                        facilityusers[-1].save()
                        logging.info("Created facility user '%s/%s'"%(facility.name,usernames[cur_usernum]))
                    cur_usernum += 1

        return (facilityusers,groups,facilities)
        

    @staticmethod
    def generateFakeExerciseLogs(topics=topics,facilityusers=None):
        if not facilityusers:
            (facilityusers,_,_) = generateFakeFacilityUsers()
            
        for topic in topics:
            exercises = json.load(open("./static/data/topicdata/" + topic + ".json","r"))
            exercises = sorted(exercises, key = lambda k: (k["h_position"], k["v_position"]))
            
            # Determine proficiency
            exercises_a = [random.random() for i in range(len(exercises))]
            exercises_b = [float(i) / len(exercises) for i in range(len(exercises))]
            
            for j, exercise in enumerate(exercises):
                for i, user in enumerate(facilityusers):
                    sig = sigmoid(proficiency[i], exercises_a[j], exercises_b[j])
                    if random.random() < 0.05 * (1-sig) and j > 2:
                        break
                    if random.random() < 0.15:
                        continue
                        
                    attempts = random.random() * 30 + 10
                    streak_progress = max(10, 10*min(10, round(attempts * sqrt(random.random() * sig)))) # should be in increments of 10
                    points   = attempts * 10 * sig
                    
                    logging.info("Creating exercise log: %-12s: %-25s (%d points, %d attempts, %d%% streak)"%(user.first_name, exercise["name"],  int(points), int(attempts), int(streak_progress)))
                    start_time = datetime.datetime.now() - datetime.timedelta(seconds=sqrt(random.random()*(1-sig))*250) # the better you are (higher sig), the faster you are!
                    UserLog.update_user_activity(user, activity_type="login", update_time=start_time)
                    elog = ExerciseLog(user=user, exercise_id=exercise["name"], attempts=int(attempts), streak_progress=int(streak_progress), points=int(points))
                    elog.full_clean(); elog.save()
                    UserLog.update_user_activity(user, activity_type="logout")
                    
            
    @staticmethod
    def generateFakeVideoLogs(topics=topics,facilityusers=None):
        if not facilityusers:
            (facilityusers,_,_) = generateFakeFacilityUsers()
            
        for topic in topics:
            videos = get_videos_for_topic(topic_id=topic)
            
            # Determine proficiency
            videos_a = [random.random() for i in range(len(videos))]
            videos_b = [float(i) / len(videos) for i in range(len(videos))]

            for j, video in enumerate(videos):
                for i, user in enumerate(facilityusers):
                    sig = sigmoid(proficiency[i], videos_a[j], videos_b[j])
                    if random.random() > sig:
                        continue
                    
                    p_complete = sqrt(sqrt(sig))
                    total_seconds_watched = video["duration"] if p_complete>=random.random() else video["duration"]*sqrt(random.random()*sig)
                    points   = total_seconds_watched/10*10

                    logging.info("Creating video log: %-12s: %-45s (%4.1f%% watched, %d points)%s"%(user.first_name, video["title"],  100*total_seconds_watched/video["duration"], int(points)," COMPLETE!" if int(total_seconds_watched)==video["duration"] else ""))
                    start_time = datetime.datetime.now()-datetime.timedelta(seconds=total_seconds_watched)
                    UserLog.update_user_activity(user, activity_type="login", update_time=start_time)
                    vlog = VideoLog(user=user, youtube_id=video["youtube_id"], total_seconds_watched=int(total_seconds_watched), points=int(points))
                    vlog.full_clean(); vlog.save()
                    UserLog.update_user_activity(user, activity_type="logout")
            