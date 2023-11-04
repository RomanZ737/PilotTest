from django.urls import path


from . import views

app_name = 'DBLoad'

urlpatterns = [
    path('alter_results/', views.alter_results, name='alter_results'),
    ]