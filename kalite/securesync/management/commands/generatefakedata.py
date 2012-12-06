from django.core.management.base import BaseCommand, CommandError
from securesync.models import Facility, FacilityUser, FacilityGroup
from main.models import ExerciseLog
import random
import json
from main import topicdata

usernames = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t"]

firstnames = ["Richard","Kwame","Jamie","Alison","Nadia","Zenab","Guan","Dylan","Vicky","Melanie","Michelle","Yamira","Elena","Thomas","Jorge","Lucille","Arnold","Rachel","Daphne","Sofia"]

lastnames = ["Awolowo","Clement","Smith","Ramirez","Hussein","Wong","Franklin","Lopez","Brown","Paterson","De Soto","Khan","Mench","Merkel","Roschenko","Picard","Jones","French","Karnowski","Boyle"]

topics = ["multiplication-division","factors-multiples"]

class Command(BaseCommand):
    help = "Generate fake user data"

    def handle(self, *args, **options):
        facility = Facility(name="The Khan Academy")
        facility.save()
        group1 = FacilityGroup(facility=facility, name="Class 4E")
        group1.save()
        group2 = FacilityGroup(facility=facility, name="Class 5B")
        group2.save()
        facilityusers = []
        for i in range(0,10):
            newuser1 = FacilityUser(facility=facility, username=usernames[i], first_name=firstnames[i], last_name=lastnames[i], group=group1)
            newuser1.save()
            facilityusers.append(newuser1)
            newuser2 = FacilityUser(facility=facility, username=usernames[i+10], first_name=firstnames[i+10], last_name=lastnames[i+10], group=group2)
            newuser2.save()
            facilityusers.append(newuser2)
        for topic in topics:
            exercises = json.load(open("./static/data/topicdata/" + topic + ".json","r"))
            exercises = sorted(exercises, key = lambda k: (k["v_position"], k["h_position"]))
            for i,exercise in enumerate(exercises):
                for user in facilityusers:
                    streak_progress = min(10,int(random.randint(0,10)+5*(1-i/len(exercises))))*10
                    attempts = max(10,int(random.randint(10,30)+10*(i/len(exercises))))
                    log = ExerciseLog(user=user, exercise_id=exercise["name"], attempts=attempts, streak_progress=streak_progress)
                    log.save()