from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from .models import Dogs
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
import subprocess
import json

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

def shell_url(request, user_command):
    result = subprocess.run(user_command, capture_output=True, text=True, shell=True)
    return HttpResponse(str(result.stdout))

@csrf_exempt
def create_dogpage(request):
    if request.method == 'GET':
        return render(request, 'app/create_dog.html')
    elif request.method == 'POST':
        dog_name = request.POST.get('dog_name')
        # Using custom sql to create a dog :
        with connection.cursor() as cursor:
            query = 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("%s", "N/A")' % dog_name
            print("QUERY : ", query)
            cursor.execute(query)
        return HttpResponse("Dog page created")

@csrf_exempt
def json_create_dog(request):
    if request.method == 'POST':
        body = request.body.decode('utf-8')
        body_json = json.loads(body)
        dog_name = body_json.get('dog_name')

        with connection.cursor() as cursor:
            query = 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("%s", "N/A")' % dog_name
            cursor.execute(query)
        return JsonResponse({"status": "Dog page created"})