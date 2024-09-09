from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dogpage/<int:dog_id>", views.dog_page, name="dog_page"),
    path("create", views.create_dogpage, name="create")
]
