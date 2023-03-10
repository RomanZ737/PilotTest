from django.urls import path


from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', start, name='start'),
    path('next_question/', next_question, name='next_question'),
    path('one_them_q/', one_them_q, name='one_them_q'),
    path('tests_results_list/', tests_results_list, name='tests_results_list'),
    path('tests_results_list/<int:id>/', test_result_details, name='test_result_details'),
    path('question_list/', question_list, name='question_list'),
    path('question_list/<int:id>/', question_list_details, name='question_list_details'),
    path('download_test_result/<int:id>/', download_test_result, name='download_test_result')

]