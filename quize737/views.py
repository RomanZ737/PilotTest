from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.utils.timezone import now

from .models import QuestionSet, QuizeSet
from django.http import HttpResponse
from .forms import *
import random


# Заглавная страница
def start(request):
    if request.method == 'POST':
        # Формируем тест на основании заданных параметров, из каждой темы по N вопросов
        all_theme_set = []
        particular_user_questions = []
        thems_num = Thems.objects.all().count()  # Общее количкство тем

        # Перебираем темы вопросов
        for theme in Thems.objects.all():
            quiz_set = QuestionSet.objects.filter(them_name=theme)
            quiz_set = random.sample(list(quiz_set), int(request.POST.get("q_num")))
            all_theme_set.append(quiz_set)
            # Сохраняем вопросы для пользователя в базу

            # Добавляем номер вопроса в объект теста для пользоваетеля
            for we in quiz_set:
                particular_user_questions.append(str(we.id))
        #DEBUG PRINT
        print(f'int(thems_num): {int(thems_num)} * int(request.POST.get("q_num")): {int(request.POST.get("q_num"))} = {int(thems_num) * int(request.POST.get("q_num"))}')
        total_q_num_for_user = int(thems_num) * int(request.POST.get("q_num"))
        QuizeSet(
            quize_name=str(request.POST.get("user_name") + request.POST.get("q_num")).replace(' ', ''),
            user_under_test=request.POST.get("user_name"),
            questions_ids=' '.join(particular_user_questions),
            # Переводим список номеров вопросов в троку для хранения в поле базы данных
            q_sequence_num=total_q_num_for_user
            # Вычисляем общее количество вопросов и добавдяем их в поле
        ).save()
        # -------  В этом месте генерируем первый вопрос теста пользователя
        # Имя теста конкретного пользователя
        user_set_name = str(request.POST.get("user_name") + request.POST.get("q_num")).replace(' ', '')

        # Выясняем количество сгенерированных вопросов
        q_amount = QuizeSet.objects.filter(quize_name=user_set_name).values('q_sequence_num')

        # Выясняем сквозные номера вопросов, сгенерированные пользователю
        q_num_list = QuizeSet.objects.filter(quize_name=user_set_name).values('questions_ids')

        # Создаём список со сгенерированными вопросами
        q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

        # Достаём из базы вопросов первый вопрос с конца
        sequence_number = (int(q_amount[0][
                 'q_sequence_num']) - 1)  # Номер вопроса в списке вопросв польхователя
        question_pisition = q_num_list[sequence_number]  # Номер вопроса в списке вопросов пользователя

        #DEBUG PRINT
        print('question_pisition: ', question_pisition, 'sequence_number: ', sequence_number)

        # Достаём нужный вопрос из базы вопросов по сквозному номеру
        question = QuestionSet.objects.filter(id=question_pisition).values()

        # Формируем данные для отправки на страницу тестирования


        # Обновляем количество оставшихся вопросов
        QuizeSet.objects.filter(quize_name=user_set_name).update(q_sequence_num=sequence_number)

        # Создаём запись с результатами теста
        QuizeResults(
            user_name=request.POST.get('user_name'),
            quize_name=user_set_name,
            total_num_q=int(q_amount[0]['q_sequence_num']),
            questions_ids=[x for x in q_num_list],
            correct_q_num=0,
            score_number=0
        ).save()
        results_object_id = QuizeResults.objects.filter(user_name=request.POST.get('user_name')).values('id')
        context = {'user': request.POST.get("user_name"), 'question': question, 'user_set_name': user_set_name, 'results_object_id': results_object_id}

        return render(request, 'start_test.html', context=context)

    else:
        return render(request, 'start.html')

# Генерация последующих вопросов
def next_question(request):
    # Проверяем нажал ли пользователь кнопку "ответить"
    if request.method == 'POST':

        # Сравниваем результат ответа
        print('user_set_name: ', request.POST.get('user_set_name'))
        print('correct_answer: ', request.POST.get('answer'))
        print('user_answer:', request.POST.get('user_answer'))
        print('results_object_id:', request.POST.get('results_object_id'))

        if request.POST.get('answer') == request.POST.get('user_answer'):
            user_score_number = QuizeResults.objects.filter(id=request.POST.get('results_object_id')).values('correct_q_num')
            QuizeResults.objects.filter(id=request.POST.get('results_object_id'))

            QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(q_sequence_num=sequence_number)

        # Количество оставшихся у пользователя вопросов
        q_amount = QuizeSet.objects.filter(quize_name=request.POST.get('user_set_name')).values('q_sequence_num')

        # Номера вопросов сгенерированные пользователю
        q_num_list = QuizeSet.objects.filter(quize_name=request.POST.get('user_set_name')).values('questions_ids')
        # Проверяем остались ли ещё вопросы в тесте польхователя
        if int(q_amount[0]['q_sequence_num']) > 0:
            q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

            # Номер позиции вопроса в списке
            question_pisition = q_num_list[int(q_amount[0]['q_sequence_num']) - 1]

            # Достаём нужный вопрос из базы вопросов по сквозному номеру
            question = QuestionSet.objects.filter(id=question_pisition).values()

            # Формируем данные для отправки на страницу тестирования
            context = {'user': request.POST.get("user_name"),
                       'question': question}

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
