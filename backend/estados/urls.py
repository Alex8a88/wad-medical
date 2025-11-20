from django.urls import path
from . import views

urlpatterns = [
    path('', views.estados_list, name='estados_list'),
]