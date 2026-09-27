from django.urls import path

from . import views


app_name = "chores"

urlpatterns = [
    path("", views.chore_list, name="list"),
]
