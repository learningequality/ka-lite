from behave import *
from kalite.testing.behave_helpers import *
from django.contrib.auth.models import User

@given("I am on the homepage")
def step_impl(context):
	if not User.objects.exists():
		User.objects.create_superuser(username='superusername', password='superpassword', email='super@email.com')
	go_to_homepage(context)