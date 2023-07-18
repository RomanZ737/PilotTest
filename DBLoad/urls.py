from django.urls import path


from . import views

app_name = 'DBLoad'

urlpatterns = [
    path('alter_questions/', views.alter_questions, name='alter_questions'),
    ]