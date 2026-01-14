from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("app/", include("sample_app.urls")),
    path('admin/', admin.site.urls),
]
