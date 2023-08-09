from django import forms
from django.contrib.auth.models import User, Group
# from models import Profile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordResetForm
from .models import UserTests, GroupsDescription
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ValidationError

import users.models


class ProfileForm(forms.ModelForm):
    class Meta:
        model = users.models.Profile
        fields = ('family_name', 'first_name', 'middle_name', 'position', 'ac_type')


#  Редактируем параметры польхователя
class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = {'username', 'email'}
        error_messages = {'email': {'invalid': "Не правильный формат поля 'Email'"}}


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# class LoginForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ("username", "password")
#         labels = {
#             'username': 'Логин',
#             'password': 'Пароль'
#         }
#         widgets = {
#             'username': forms.Select(attrs={'size': 3}),
#             "password": forms.PasswordInput(attrs={'style': 'font-size: 25'})
#         }

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': ''}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': ''}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'style': 'font-size: 25px;'})
        self.fields['username'].label = 'Логин:'
        self.fields['password'].widget.attrs.update({'style': 'font-size: 25px;'})
        self.fields['password'].label = 'Пароль:'


class RestorePasword(PasswordResetForm):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'style': 'font-size: 25px;'})
        # self.fields['username'].label = 'Логин:'


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


# Форма теста для пользователя
class TestsForUser(forms.ModelForm):
    class Meta:
        model = UserTests
        fields = {'test_name', 'num_try', 'date_before'}
        widgets = {
            'date_before': forms.SelectDateWidget(months=MONTH_CHOICES),
            'num_try': forms.NumberInput(attrs={'step': 1, 'min': 1, 'size': '3'})
        }
        error_messages = {'num_try': {'required': "Поле количества вопросов не может быть пустым"},
                          'test_name': {'required': "Поле 'Название теста' не может быть пустым"}}


# Валидатор для формы GroupForm - проверят уникальность имени группы
def similar_group_name(value):
    group_name = Group.objects.filter(name=value)
    if len(group_name) > 0:
        raise ValidationError('Группа с таким именем уже существует')


# Форма группы новой для пользователя
class GroupForm(forms.ModelForm):
    class Meta:
        model = GroupsDescription
        # fields = {'group', 'discription'}
        exclude = ('group',)
        widgets = {
            'discription': forms.Textarea(attrs={'cols': 70, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        # self.fields['user_defined_code'] = forms.ModelChoiceField(queryset=UserDefinedCode.objects.filter(owner=user))
        self.fields['group_name'] = forms.CharField(widget=forms.Textarea(attrs={"cols": "50", 'rows': "1"}))
        self.fields['group_name'].validators = [similar_group_name]


# Форма для редактирования существующей группы
class EditGroupForm(forms.ModelForm):
    class Meta:
        model = GroupsDescription
        # fields = {'group', 'discription'}
        exclude = ('group',)
        widgets = {
            'discription': forms.Textarea(attrs={'cols': 70, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super(EditGroupForm, self).__init__(*args, **kwargs)
        # self.fields['user_defined_code'] = forms.ModelChoiceField(queryset=UserDefinedCode.objects.filter(owner=user))
        self.fields['group_name'] = forms.CharField(widget=forms.Textarea(attrs={"cols": "50", 'rows': "1"}))
    # widgets = {
    #     'group': forms.TextInput(),
    #     'discription': forms.TextInput()}
