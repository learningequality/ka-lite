from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect

def problem_attempt(request, exercise, num):
    print exercise, num
    return HttpResponse({})