from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Dogs
from django.db import connection
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
    return HttpResponse("Your dog, %s, is lovely. Boss name is : %s" % (dog.dog_name, dog.dog_boss))

def create_dogpage(request, dog_name):
#    dog = Dogs(dog_name=dog_name, dog_boss="Unset")
#    dog.save()
    # Using custom sql to create a dog :
    with connection.cursor() as cursor:
        query = 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("%s", "N/A")' % dog_name
        print("QUERY : ", query)
        cursor.execute(query)
    return HttpResponse("Dog page created")

def create(request):
    template = loader.get_template("app/create_dog.html")
    return HttpResponse(template.render({}, request))
