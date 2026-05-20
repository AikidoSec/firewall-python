from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Dogs
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess

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


# --- bypass regression endpoints ---

@csrf_exempt
def read_file(request):
    # Passes raw bytes body directly to open() — path traversal sink.
    # Used by AIKIDO-5RDTZW1V regression test: a leading \xff byte must not
    # prevent the firewall from detecting the traversal in the rest of the path.
    if request.method == 'POST':
        with open(request.body) as f:
            return HttpResponse(f.read())
    return HttpResponse("Use POST")


@csrf_exempt
def json_sql(request):
    # Parses body via json.loads(bytes) without relying on Content-Type.
    # Used by AIKIDO-B3YABOSP regression test: surrogate bytes (\xed\xa0\x80)
    # embedded in the JSON body must not prevent the firewall from parsing the
    # body and detecting the SQL injection payload.
    if request.method == 'POST':
        data = json.loads(request.body)
        dog_name = data.get('dog_name', '')
        with connection.cursor() as cursor:
            query = 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("%s", "N/A")' % dog_name
            cursor.execute(query)
        return HttpResponse("OK")
    return HttpResponse("Use POST")
