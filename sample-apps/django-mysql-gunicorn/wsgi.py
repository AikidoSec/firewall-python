import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample-django-mysql-gunicorn-app.settings')

application = get_wsgi_application()
