from django.core.management.base import BaseCommand, CommandError
from securesync.models import Facility, FacilityUser, FacilityGroup
from main.models import ExerciseLog
import random
import json
from math import exp
from main import topicdata

def sigmoid(theta, a, b):
    return 1.0 / (1.0 + exp(b - a * theta))

firstnames = ["Richard","Kwame","Jamie","Alison","Nadia","Zenab","Guan","Dylan","Vicky","Melanie","Michelle","Yamira","Elena","Thomas","Jorge","Lucille","Arnold","Rachel","Daphne","Sofia"]

lastnames = ["Awolowo","Clement","Smith","Ramirez","Hussein","Wong","Franklin","Lopez","Brown","Paterson","De Soto","Khan","Mench","Merkel","Roschenko","Picard","Jones","French","Karnowski","Boyle"]

usernames = [firstname[0].lower() + lastname.lower() for firstname, lastname in zip(firstnames, lastnames)]

proficiency = [random.random() * 0.8 for i in range(10)] + [random.random() for i in range(10)]

topics = ["multiplication-division", "factors-multiples"]

class Command(BaseCommand):
    help = "Generate fake user data"

    def handle(self, *args, **options):
        facility = Facility(name="Wilson Elementary")
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
            exercises = sorted(exercises, key = lambda k: (k["h_position"], k["v_position"]))
            exercises_a = [random.random() for i in range(len(exercises))]
            exercises_b = [float(i) / len(exercises) for i in range(len(exercises))]
            for i, user in enumerate(facilityusers):
                for j, exercise in enumerate(exercises):
                    sig = sigmoid(proficiency[i], exercises_a[j], exercises_b[j])
                    if random.random() < 0.05 * (1-sig) and j > 2:
                        break
                    if random.random() < 0.15:
                        continue
                    attempts = random.random() * 40 + 10
                    streak_progress = max(10, min(100, 10 * random.random() + 10 * attempts * sig))
                    print int(attempts), int(streak_progress), user.first_name, exercise["name"]
                    log = ExerciseLog(user=user, exercise_id=exercise["name"], attempts=attempts, streak_progress=streak_progress)
                    log.save()
                    