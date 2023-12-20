from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'dbLogs'

urlpatterns = [
    path('user_log/', views.user_log, name='user_log'),
    ]