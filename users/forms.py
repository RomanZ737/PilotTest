from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

import users.models

class ProfileForm(forms.ModelForm):

    class Meta:
        model = users.models.Profile
        fields = ('family_name', 'first_name', 'middle_name', 'position')




class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "password")
        labels = {
            'username': 'Логин',
            'password': 'Пароль'
        }
