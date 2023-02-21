from django.urls import path


from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', start, name='start'),
    path('next_question/', next_question, name='next_question'),
    path('one_them_q/', one_them_q, name='one_them_q')

]