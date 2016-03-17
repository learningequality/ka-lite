'''
This module contains all tests for the functions invoked to
get the "Explore" recommendations.
'''
import datetime

from django.test.client import RequestFactory

from django.conf import settings
from kalite.topic_tools.content_recommendation import get_explore_recommendations
from kalite.testing.base import KALiteTestCase
from kalite.facility.models import Facility, FacilityUser
from kalite.main.models import ExerciseLog

class TestExploreMethods(KALiteTestCase):

    ORIGINAL_POINTS = 37
    ORIGINAL_ATTEMPTS = 3
    ORIGINAL_STREAK_PROGRESS = 20
    NEW_POINTS_LARGER = 22
    NEW_ATTEMPTS = 5
    NEW_STREAK_PROGRESS_LARGER = 10
    NEW_POINTS_SMALLER = 0
    NEW_STREAK_PROGRESS_SMALLER = 0
    EXERCISE_ID = "number_line"
    USERNAME1 = "test_user_explore_1"
    PASSWORD = "dummies"
    FACILITY = "Test Facility Explore"
    TIMESTAMP = datetime.datetime(2014, 11, 17, 20, 51, 2, 342662)

    def setUp(self):
        '''Performed before every test'''

        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name=self.FACILITY)
        self.facility.save()

        self.user1 = FacilityUser(username=self.USERNAME1, facility=self.facility)
        self.user1.set_password(self.PASSWORD)
        self.user1.save()

        #add one exercise
        self.original_exerciselog = ExerciseLog(exercise_id=self.EXERCISE_ID, user=self.user1)
        self.original_exerciselog.points = self.ORIGINAL_POINTS
        self.original_exerciselog.attempts = self.ORIGINAL_ATTEMPTS
        self.original_exerciselog.streak_progress = self.ORIGINAL_STREAK_PROGRESS
        self.original_exerciselog.latest_activity_timestamp = self.TIMESTAMP
        self.original_exerciselog.completion_timestamp = self.TIMESTAMP
        self.original_exerciselog.save()

        #create a request factory for later instantiation of request
        self.factory = RequestFactory() 

    def test_explore_overall(self):
        '''get_explore_recommendations()'''

        #create a request object and set the language attribute
        request = self.factory.get('/content_recommender?explore=true')
        request.language = settings.LANGUAGE_CODE

        actual = get_explore_recommendations(self.user1, request)

        self.assertEqual(actual[0].get("interest_topic").get("id"), "arithmetic")
