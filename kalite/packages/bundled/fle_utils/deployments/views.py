# Create your views here.
from django.core import serializers
from django.shortcuts import render

from models import Deployment

def deployments(request):
	deployments = serializers.serialize("json", Deployment.objects.all())
	context = {
		"deployments": deployments
	}
	return render(request, "deployments.html", context)