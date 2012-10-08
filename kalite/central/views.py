import re, json
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from annoying.decorators import render_to
import settings

@render_to("central/homepage.html")
def homepage_handler(request):
    context = {}
    return context
        