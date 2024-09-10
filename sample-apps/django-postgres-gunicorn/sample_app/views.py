from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Dogs
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
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
    return HttpResponse("Your dog, %s, is lovely. Is admin? %s" % (dog.dog_name, dog.is_admin))

@csrf_exempt
def create_dogpage(request):
    if request.method == 'GET':
        return render(request, 'app/create_dog.html')
    elif request.method == 'POST':
        dog_name = request.POST.get('dog_name')
        # Using custom sql to create a dog :
        with connection.cursor() as cursor:
            query = f"INSERT INTO sample_app_Dogs (dog_name, is_admin) VALUES ('%s', FALSE)" % (dog_name)
            print("QUERY : ", query)
            cursor.execute(query)

        return HttpResponse("Dog page created")
