import psycopg
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import aget_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Dogs


async def index(request):
    dogs = [dog async for dog in Dogs.objects.all()]
    template = loader.get_template("app/index.html")
    context = {"dogs": dogs}
    return HttpResponse(template.render(context, request))


async def dog_page(request, dog_id):
    dog = await aget_object_or_404(Dogs, pk=dog_id)
    return HttpResponse("Your dog, %s, is lovely. Is admin? %s" % (dog.dog_name, dog.is_admin))


def _get_db_conninfo():
    """Build psycopg connection string from Django settings."""
    db = settings.DATABASES['default']
    return f"host={db['HOST']} port={db['PORT']} dbname={db['NAME']} user={db['USER']} password={db['PASSWORD']}"


@csrf_exempt
async def create_dogpage(request):
    if request.method == 'GET':
        template = loader.get_template("app/create_dog.html")
        return HttpResponse(template.render({}, request))
    elif request.method == 'POST':
        dog_name = request.POST.get('dog_name')
        # Use vulnerable SQL to insert the dog name, so we can test that aikido_zen is working.
        query = f"INSERT INTO sample_app_dogs (dog_name, is_admin) VALUES ('%s', FALSE)" % dog_name

        async with await psycopg.AsyncConnection.connect(_get_db_conninfo()) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)

        return HttpResponse("Dog page created")
