from django.http import HttpResponse
from annoying.decorators import render_to


@render_to("benchmarking/benchmarking.html")
def benchmarking(request):
    return HttpResponse("Welcome to benchmarking page!(why a page?)")
