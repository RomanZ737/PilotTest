from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth import login


def register(request):
    if request.method == 'POST':
        form_user = UserRegisterForm(request.POST)
        form_profile = ProfileForm(request.POST)
        if form_user.is_valid() and form_profile.is_valid():
            new_user = form_user.save(commit=False)
            new_user.set_password(form_user.cleaned_data['password1'])
            new_user.save()
            Profile.objects.create(
                user=new_user,
                family_name=form_profile.cleaned_data['family_name'],
                first_name=form_profile.cleaned_data['first_name'],
                middle_name=form_profile.cleaned_data['middle_name'],
                position=form_profile.cleaned_data['position']
            )
            new_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, new_user)

            return render(request, 'start_all_q.html')

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
    return render(request, 'profile.html')
