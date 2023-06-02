from django import forms
from django.contrib.auth.models import User
# from models import Profile
from django.contrib.auth.forms import UserCreationForm
from .models import UserTests
from django.contrib.admin.widgets import AdminDateWidget

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


# class ProfileFormReadOnly(forms.ModelForm):
#     class Meta:
#         model = users.models.Profile
#         fields = ('family_name', 'first_name', 'middle_name', 'position')
#
#     # def __init__(self, *args, **kwargs):
#     #     super(ProfileFormReadOnly, self).__init__(*args, **kwargs)
#     #     self.fields['family_name'].disabled = True
#     #     self.fields['first_name'].disabled = True
#     #     self.fields['middle_name'].disabled = True
#     #     self.fields['position'].disabled = True

# Виджеты для выбора даты и времени
MONTH_CHOICES = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
    5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
    9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}


class TestsForUser(forms.ModelForm):
    class Meta:
        model = UserTests
        fields = {'test_name', 'num_try', 'date_before'}
        widgets = {
            'date_before': forms.SelectDateWidget(months=MONTH_CHOICES),
        }
        error_messages = {'num_try': {'required': "Поле количества вопросов не может быть пустым"}, 'test_name': {'required': "Поле 'Название теста' не может быть пустым"}}