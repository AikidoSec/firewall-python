from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


def index(request):
    return HttpResponse("Hello World")

def dog_page(request, dog_id):
    return HttpResponse("Your dog with id %s is lovely." % dog_id)

def create_dogpage(request, dog_name):
    return HttpResponse("Dog page created with name %s" % dog_name)