"""PilotTest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf.urls.static import static, serve
from django.conf import settings
from users import views as users_views
from django.contrib.auth import views as auth_views
from quize737 import views as quize737_views
from users.forms import LoginForm, RestorePasword
from dbLogs import views as dbLogs_views
from django.conf import settings


from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordChangeView,
    PasswordChangeDoneView

)


urlpatterns = [
                  path('PilotAdmin/', admin.site.urls),
                  path('', quize737_views.start, name='start'),
                  path('login/', auth_views.LoginView.as_view(template_name='login.html', authentication_form=LoginForm), name='login'),
                  path('', include('quize737.urls', namespace='quize737')),
                  path('', include('dbLogs.urls', namespace='dbLogs')),
                  path('DBLoad/', include('DBLoad.urls', namespace='DBLoad')),
                  path('quiz/', include('quiz.urls', namespace='quiz')),
                  path('profile/', users_views.profile, name='profile'),
                  path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
                  path('register/', users_views.register, name='register'),
                  path('password-reset/', PasswordResetView.as_view(template_name='password_reset.html', html_email_template_name='password_reset_email.html', form_class=RestorePasword), name='password-reset'),
                  path('password-reset/done/', PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
                  path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
                  path('password-reset-complete/', PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
                  #path('password_change/', PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
                  path('password_change/', users_views.password_change, name='password_change'),
                  path('password_change_done/', PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
                  re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
                  re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
              ] \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
