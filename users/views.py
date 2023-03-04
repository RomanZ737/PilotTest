from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile

def register(request):
    if request.method == 'POST':
        form_user = UserRegisterForm(request.POST)
        form_profile = ProfileForm(request.POST)
        if form_user.is_valid() and form_profile.is_valid():
            new_user = form_user.save(commit=False)
            new_user.set_password(form_user.cleaned_data['password1'])
            new_user.save()
            print(form_profile)
            Profile.objects.create(
                user=new_user,
                family_name=form_profile.cleaned_data['family_name'],
                first_name=form_profile.cleaned_data['first_name'],
                middle_name=form_profile.cleaned_data['middle_name'],
                position=form_profile.cleaned_data['position']
            )


            return render(request, 'start_all_q.html')

        else:
            print('Here3')

            messages.error(request, f'Исправьте ошибки!')

    else:
        form_user = UserRegisterForm()
        form_profile= ProfileForm()
        context = {'form_user': form_user, 'form_profile': form_profile}
        return render(request, 'register.html', context=context)


@login_required
def profile(request):
    return render(request, 'profile.html')
