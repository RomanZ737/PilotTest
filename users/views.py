from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegisterForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from .models import Profile, UserTests
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordChangeDoneView

)

@login_required
def register(request):
    if request.method == 'POST':
        form_user = UserRegisterForm(request.POST)
        form_profile = ProfileForm(request.POST)
        if form_user.is_valid() and form_profile.is_valid():
            group = Group.objects.get(name=form_profile.cleaned_data['position'])
            new_user = form_user.save(commit=False)
            new_user.set_password(form_user.cleaned_data['password1'])
            new_user.save()
            new_user.groups.add(group)
            Profile.objects.create(
                user=new_user,
                family_name=form_profile.cleaned_data['family_name'],
                first_name=form_profile.cleaned_data['first_name'],
                middle_name=form_profile.cleaned_data['middle_name'],
                position=form_profile.cleaned_data['position']
            )
            new_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, new_user)

            return render(request, 'start.html')

        else:
            err_list = []
            for err_1 in dict(form_user.errors).keys():
                print('err_1: ', err_1)
                print('form_user.errors: ', dict(form_user.errors)[err_1].as_json(escape_html=False))
                if err_1 == 'email':
                    err_list.append('Ввведите корретный email')
                elif 'password' in err_1:
                    if 'This password is too short' in dict(form_user.errors)[err_1].as_json(escape_html=False):
                        err_list.append('Пароль слишком короткий')
                    else:
                        err_list.append('Пароли не совпадают')

            print('err_list: ', err_list)
            print('ERRORS: ', form_profile.errors.as_json())
            print('ERRORS2: ', form_user.errors.as_json(escape_html=True))
            context = {'form_user': form_user, 'form_profile': form_profile, 'err_list': err_list}

            return render(request, 'register.html', context=context)

    else:
        form_user = UserRegisterForm()
        form_profile = ProfileForm()
        context = {'form_user': form_user, 'form_profile': form_profile}
        return render(request, 'register.html', context=context)


@login_required
def profile(request):
    user_tests = UserTests.objects.filter(user=request.user)
    chang_pass_form = PasswordChangeView()
    print('chang_pass_form:', dir(chang_pass_form))
    print('chang_pass_form:', chang_pass_form)
    context = {'change_pass_form': chang_pass_form, 'user_tests': user_tests}
    return render(request, 'profile.html', context=context)

@login_required
def password_change(request):
    user_tests = UserTests.objects.filter(user=request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)   # Обновляем данные сессии пользователя, что бы он сотавался залогиненым после смены пароля
            test_and_data_saved = True
            context = {'form': form, 'user_tests': user_tests, 'test_and_data_saved': test_and_data_saved}
            return render(request, 'password_change.html', context=context)
    else:
        form = PasswordChangeForm(request.user)
        context = {'form': form, 'user_tests': user_tests}
        return render(request, 'password_change.html', context=context)



