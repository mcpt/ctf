from django.urls import path

from . import views

urlpatterns = [path("ctftime/<int:contest_id>", views.CtfTime, name="ctftime_export")]
