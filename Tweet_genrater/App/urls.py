from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    path('', views.index, name='index'),  # Home page
    path('generate_tweet/', views.generate_tweet, name='generate_tweet'),  # URL to generate tweets
]
