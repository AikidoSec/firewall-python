from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Dogs
# Create your views here.


def index(request):
    dogs = Dogs.objects.all()
    print(dogs)
    template = loader.get_template("app/index.html")
    context = {
        "dogs": dogs,
    }
    return HttpResponse(template.render(context, request))


def dog_page(request, dog_id):
    dog = get_object_or_404(Dogs, pk=dog_id)
    return HttpResponse("Your dog, %s, is lovely." % dog.dog_name)

def create_dogpage(request, dog_name):
    dog = Dogs(dog_name=dog_name, dog_boss="Unset")
    dog.save()
    return HttpResponse("Dog page created with id %s" % dog.id)