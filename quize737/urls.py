from django.urls import path


from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', start, name='start'),
    path('addQuestion/', addQuestion, name='addQuestion'),
    path('login/', loginPage, name='login'),
    path('logout/', logoutPage, name='logout'),
    path('register/', registerPage, name='register'),
    path('next_question/', next_question, name='next_question')

]