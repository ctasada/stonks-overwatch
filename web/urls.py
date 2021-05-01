from django.urls import path
from web import views

urlpatterns = [
    path('', views.web, name='web'),
]