from django.urls import path

from . import views

urlpatterns = [path("ctftime", views.CtfTime, name="ctftime_export")]
