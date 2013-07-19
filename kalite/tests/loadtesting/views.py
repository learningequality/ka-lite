from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from annoying.decorators import render_to
from config.models import Settings

@render_to("loadtesting/load_test.html")
def load_test(request):
    return {}