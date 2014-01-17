from annoying.decorators import render_to

from models import ExperimentLog

from random import randint
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

def control_flow(request):
	user = request.session.get("facility_user")
	(experiment, was_created) = ExperimentLog.get_or_initialize(user=user)
	if was_created:
		experiment.condition = randint(0,2)
		experiment.save()
	print experiment.activity_stage
	if request.GET.get("next", "")=="true" and experiment.activity_stage in [0,1,2,4,7,8]:
		experiment.activity_stage += 1
		experiment.save()
	if request.GET.get("next", "")=="test" and experiment.activity_stage in [3,6]:
		experiment.activity_stage += 1
		experiment.save()
	if ((experiment.start_datetime + timedelta(days=4)).replace(hour=0, minute=0) < datetime.now()) and (4 <= experiment.activity_stage < 6):
		experiment.activity_stage += 1
		experiment.save()
	if experiment.condition == 2 and request.GET.get("time", "") and request.GET.get("date", ""):
		time = request.GET.get("time")
		date = request.GET.get("date")
		experiment.datacollect = time + " " + date
		experiment.activity_stage += 1
		experiment.save()
		return HttpResponseRedirect(reverse("control_flow"))
	if experiment.activity_stage == 0:
		return instructions(request)
	if 0 < experiment.activity_stage < 3 or experiment.activity_stage == 8:
		return survey1(request, experiment.activity_stage)

	elif experiment.activity_stage == 7:
		if experiment.condition == 0:
			survey = 4
		else:
			survey = 3
		return survey1(request, survey)

	elif experiment.activity_stage == 3:
		test = 1
		return HttpResponseRedirect(reverse("test", args=(test,)))
	elif experiment.activity_stage == 6:
		test = 2
		return HttpResponseRedirect(reverse("test", args=(test,)))
	elif experiment.activity_stage == 4:
		return time_pick(request, experiment)
	elif experiment.activity_stage == 5:
		return HttpResponseRedirect("../math/trigonometry/polynomial_and_rational/quad_formula_tutorial/")
	elif experiment.activity_stage == 9:
		experiment.end_datetime = datetime.now()
		experiment.save()
		return complete(request, user)

@render_to("research/survey1.html")
def survey1(request, survey):
    """
    Display a survey
    """

    user = request.session.get("facility_user")
    survey_urls = {
    	1: "https://docs.google.com/forms/d/1KRWOLwPdFKtWrV8651OkStN1neKFO_1aVGpn-TCgsXY/viewform?entry.2112932773",
    	2: "https://docs.google.com/forms/d/1SmhkF8g5MhHC6VPdZEkbF5RxLWtIRydV6LQXbr56Sks/viewform?entry.1651397965",
    	3: "https://docs.google.com/forms/d/1JHU8BjLpTe45Ey_ChSWZd8u-l0SCmdmnTnV3FYkX-lw/viewform?entry.1921541933",
    	4: "https://docs.google.com/forms/d/1u_F7Wnj_shd6PiIKh_KO4VQXQqhA61I38ddyFLBw2kI/viewform?entry.1921541933",
    	8: "https://docs.google.com/forms/d/1-yVnVFrVVauAefvPKkkUJP9O8UthtFxUUvgYSi9iqs4/viewform?entry.1651397965",
    }
    survey_url = survey_urls[survey]

    context = {
        "user": user,
        "survey_url": survey_url,
    }
    return context

@render_to("research/timepick.html")
def time_pick(request, experiment):
    """
    Display the time picker
    """

    user = request.session.get("facility_user")
    test_time = (experiment.start_datetime+timedelta(days=4)).replace(hour=0, minute=0).strftime('%A, %B %d')
    if experiment.condition == 1:
    	time = (experiment.start_datetime+timedelta(days=2)).replace(hour=18, second=0).strftime('%A, %B %d at %I:%M%p')
    	experiment.datacollect = time
    	experiment.save()
    else:
    	time = ""
    context = {
        "user": user,
        "time": time,
        "test_time": test_time,
        "condition": experiment.condition,
    }
    return context

@render_to("research/complete.html")
def complete(request, user):
	"""Show as complete"""
	redirect_url = "https://ucsd.sona-systems.com/webstudy_credit.aspx?experiment_id=469&credit_token=49fc42158dca467d84e438af03608a05&survey_code=%s" % user.username
	context = {
		"redirect_url": redirect_url
	}
	return context

@render_to("research/instructions.html")
def instructions(request):
	"""Show instructions"""
	return {}