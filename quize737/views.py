from django.shortcuts import render, redirect
from django.contrib.auth import login,logout,authenticate
from .models import QuestionSet, QuizeSet
from django.http import HttpResponse
from .forms import *
import random


# Create your views here.
def start(request):
    if request.method == 'POST':
        # Формируем тест на основании заданных параметров, из каждой темы по N вопросов
        all_theme_set = []
        for theme in Thems.objects.all():
            quiz_set = QuestionSet.objects.filter(them_name=theme)
            quiz_set = random.sample(list(quiz_set), int(request.POST.get("q_num")))
            # Сохраняем вопросы для пользователя в базу
            QuizeSet.objects.bulk_create([QuizeSet(**{'batch_cola': m[0],
                                                    'batch_colb': m[1],
                                                    'batch_colc': m[2],
                                                    'batch_cold': m[3],
                                                    'batch_cole': m[4]})
                                         for m in quiz_set])

            all_theme_set.append(quiz_set)
        context = {'all_theme_set': all_theme_set, 'user': request.POST.get("user_name")}

        return render(request, 'all_them_set.html', context=context)

    else:
        return render(request, 'start.html')

def index(request):
    if request.method == 'POST':
        print(request.POST)
        questions = QuestionSet.objects.all()
        score = 0
        wrong = 0
        correct = 0
        total = 0
        for q in questions:
            total += 1
            print(request.POST.get(q.question))
            print(q.answer)
            print()
            if q.answer == int(request.POST.get(q.question)):
                score += 10
                correct += 1
            else:
                wrong += 1
        percent = score / (total * 10) * 100
        context = {
            'score': score,
            'time': request.POST.get('timer'),
            'correct': correct,
            'wrong': wrong,
            'percent': percent,
            'total': total,
            'search': request.POST.get("Maximum start EGT")
        }
        return render(request, 'result.html', context)
    else:
        questions = QuestionSet.objects.all()
        context = {
            'questions': questions
        }
        return render(request, 'index.html', context)


def addQuestion(request):
    if request.user.is_staff:
        form = addQuestionform()
        if request.method == 'POST':
            form = addQuestionform(request.POST)
            if form.is_valid():
                form.save()
                return redirect('/')
        context = {'form': form}
        return render(request, 'addQuestion.html', context)
    else:
        return redirect('home')


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = createuserform()
        if request.method == 'POST':
            form = createuserform(request.POST)
            if form.is_valid():
                user = form.save()
                return redirect('login')
        context = {
            'form': form,
        }
        return render(request, 'register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
        context = {}
        return render(request, 'login.html', context)


def logoutPage(request):
    logout(request)
    return redirect('/')

