from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.utils.timezone import now

from .models import QuestionSet, QuizeSet
from django.http import HttpResponse
from .forms import *
import random


# Create your views here.
def start(request):
    if request.method == 'POST':
        # Формируем тест на основании заданных параметров, из каждой темы по N вопросов
        all_theme_set = []
        particular_user_questions = []
        thems_num = Thems.objects.all().count()  # Обзее количкство тем

        for theme in Thems.objects.all():
            quiz_set = QuestionSet.objects.filter(them_name=theme)
            quiz_set = random.sample(list(quiz_set), int(request.POST.get("q_num")))
            all_theme_set.append(quiz_set)
            # Сохраняем вопросы для пользователя в базу
            for we in quiz_set:
                particular_user_questions.append(str(we.id))
        QuizeSet(
            quize_name=str(request.POST.get("user_name") + request.POST.get("q_num")).replace(' ', ''),
            user_under_test=request.POST.get("user_name"),
            questions_ids=' '.join(particular_user_questions),
            q_sequence_num=thems_num * int(request.POST.get("q_num"))  # Вычисляем общее количество вопросов
        ).save()

        # Имя теста конкретного пользователя
        user_set_name = str(request.POST.get("user_name") + request.POST.get("q_num")).replace(' ', '')
        # Выясняем количество сгенерированных вопросов
        q_amount = QuizeSet.objects.filter(quize_name=user_set_name).values('q_sequence_num')
        q_num_list = QuizeSet.objects.filter(quize_name=user_set_name).values('questions_ids')
        # Создаём список со сгенерированными вопросами
        q_num_list = list((q_num_list[0]['questions_ids']).split(' '))
        user_quize = QuizeSet.objects.all().values
        # Достаём из базы вопросов первый вопрос с конца
        question_pisition = q_num_list[int(q_amount[0][
                                               'q_sequence_num']) - 2]  # Номер позиции вопроса в списке вопросов пользователя (первый разот вычитаем 2 т.е. нумерация в списке начинается с 0)
        question = QuestionSet.objects.filter(id=question_pisition).values()
        context = {'all_theme_set': all_theme_set, 'user': request.POST.get("user_name"), 'user_quize': user_quize,
                   'q_amount': q_amount, 'q_num_list': q_num_list, 'question': question}
        # Обновляем количество оставшихся вопросов
        QuizeSet.objects.filter(quize_name=user_set_name).update(q_sequence_num=question_pisition)

        return render(request, 'start_test.html', context=context)

    else:
        return render(request, 'start.html')


def next_question(request):

    context = {'post_data': request.POST}
    return render(request, 'start_test.html', context=context)


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
