# -*- coding: utf-8 -*-

import os
import random
import io

from django.core.exceptions import PermissionDenied
from django.utils import six
from django.shortcuts import render, redirect
from .models import QuestionSet, QuizeSet, Thems, QuizeResults
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from .forms import QuestionSetForm
from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics  # Библиотека для формирования pdf файла
from reportlab.lib.units import inch  # Библиотека для формирования pdf файла
from reportlab.pdfbase.ttfonts import TTFont

from django.http import FileResponse
from reportlab.pdfgen import canvas


# Декоратор проверки группы пользователя для доступа
def group_required(group, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has a group permission,
    redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """

    def check_perms(user):
        if isinstance(group, six.string_types):
            groups = (group,)
        else:
            groups = group
        # First check if the user has the permission (even anon users)

        if user.groups.filter(name__in=groups).exists() | user.is_superuser:
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)


# Формироваине теста с вопросами из всех тем
def all_them_q_set():
    pass


# Заглавная страница + вопросы по всем темам
@login_required  # Только для зарегитсрированных пользователей
def start(request):
    if request.method == 'POST':

        # Формируем тест на основании заданных параметров, из каждой темы по N вопросов
        all_theme_set = []
        particular_user_questions = []
        thems_num = Thems.objects.all().count()  # Общее количкство тем
        max_score_number = 0  # Максимальное количество баллов по сгенерированным вопросам

        # Перебираем темы вопросов
        for theme in Thems.objects.all():
            quiz_set = QuestionSet.objects.filter(them_name=theme)
            quiz_set = random.sample(list(quiz_set), int(request.POST.get("q_num")))
            all_theme_set.append(quiz_set)
            # Сохраняем вопросы для пользователя в базу

            # Добавляем номер вопроса в объект теста для пользоваетеля
            for we in quiz_set:
                particular_user_questions.append(str(we.id))
                if we.q_weight != 0:
                    max_score_number = max_score_number + we.q_weight
                else:
                    max_score_number = max_score_number + 1

        total_q_num_for_user = int(thems_num) * int(request.POST.get("q_num"))

        user_quize_set = QuizeSet.objects.create(
            quize_name="Все Темы " + request.POST.get("q_num") + ' Вопроса(ов)',
            user_under_test=request.POST.get("user_name"),
            # Переводим список номеров вопросов в строку для хранения в поле базы данных
            questions_ids=' '.join(particular_user_questions),
            # Вычисляем общее количество вопросов и добавдяем их в поле
            q_sequence_num=total_q_num_for_user,
            # Вносим максимально возможное кол-во баллов
            max_score_amount=max_score_number
        )

        # -------  В этом месте генерируем первый вопрос теста пользователя
        # Имя теста конкретного пользователя
        user_set_name = "Все Темы " + request.POST.get("q_num") + ' Вопроса(ов)'

        # Выясняем количество сгенерированных вопросов
        q_amount = QuizeSet.objects.filter(id=user_quize_set.id).values('q_sequence_num')

        # Выясняем сквозные номера вопросов, сгенерированные пользователю
        q_num_list = QuizeSet.objects.filter(id=user_quize_set.id).values('questions_ids')

        # Создаём список со сгенерированными вопросами
        q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

        # Достаём из базы вопросов первый вопрос с конца
        sequence_number = (int(q_amount[0][
                                   'q_sequence_num']) - 1)  # Номер вопроса в списке вопросов пользователя
        question_pisition = q_num_list[sequence_number]  # Номер вопроса в списке вопросов пользователя

        # Достаём нужный вопрос из базы вопросов по сквозному номеру
        question = QuestionSet.objects.filter(id=question_pisition).values()

        # Формируем данные для отправки на страницу тестирования

        # Обновляем количество оставшихся вопросов
        QuizeSet.objects.filter(id=user_quize_set.id).update(q_sequence_num=sequence_number)

        # Создаём запись с результатами теста
        result_obj = QuizeResults.objects.create(
            user_name=request.POST.get('user_name'),
            quize_name=user_set_name,
            total_num_q=sequence_number + 1,
            questions_ids=', '.join(q_num_list),
            correct_q_num=0,
            score_number=0
        )

        context = {'user_name': request.POST.get("user_name"), 'question': question, 'user_set_id': user_quize_set.id,
                   'results_object_id': result_obj.id, 'q_kind': question[0]['q_kind']}

        # Проверяем содержит ли вопрос мультивыбор
        if question[0]['q_kind'] == False:
            q_page_layout = 'start_test_radio.html'
        else:
            q_page_layout = 'start_test_check.html'

        # DEBUG PRINT
        print('Q KIND: ', question[0]['q_kind'])
        print("q_page_layout: ", q_page_layout)

        return render(request, q_page_layout, context=context)

    else:
        return render(request, 'start_all_q.html')


# Генерация последующих вопросов
def next_question(request):
    # Проверяем нажал ли пользователь кнопку "ответить"
    if request.method == 'POST':

        # Сравниваем результат ответа
        # print("POST: ", request.POST)
        # print('Q Kind: ', request.POST.get('q_kind'))
        # print('user_set_id: ', request.POST.get('user_set_id'))
        # print('correct_answers: ', request.POST.get('answers'), 'type: ', type(request.POST.get('answers')))
        # print('user_answer:', request.POST.get('user_answer'))
        # print('results_object_id:', request.POST.get('results_object_id'))
        # print('q_weight: ', request.POST.get('q_weight'))

        # Проверяем вид вопроса
        if request.POST.get('q_kind') == 'True':

            # DEBUG PRINT
            print('МУЛЬТИОТВЕТНЫЙ ВОПРОС')

            user_answers_list = []
            for a in request.POST.keys():
                if 'user_answer' in a:
                    user_answers_list.append(request.POST[a][0])

            # Если ответ пользователя правильный
            if request.POST.get('answers') == ','.join(user_answers_list):

                # DEBUG PRINT
                print('Привильный ответ')

                # Вынимаем текущее количество правильных ответов и количество баллов пользователя
                user_result_data = QuizeResults.objects.filter(id=request.POST.get('results_object_id')).values(
                    'correct_q_num', 'score_number')

                # Увеличиваем количество правильных ответов на единицу и записыввем в базу
                QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(
                    correct_q_num=(user_result_data[0]['correct_q_num'] + 1))

                # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть
                if float(request.POST.get('q_weight')) != 0.0:
                    updated_score_number = user_result_data[0]['score_number'] + float(request.POST.get('q_weight'))

                else:
                    updated_score_number = user_result_data[0]['score_number'] + 1

                # Обновляем количетво баллов
                QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(
                    score_number=updated_score_number)
            else:
                print('Не правильный ответ')


        else:
            # DEBUG PRINT
            print('ОБЫЧНЫЙ ВОПРОС')

            # Если пользователь правильно ответил на вопрос:
            if request.POST.get('answer') == request.POST.get('user_answer'):

                # DEBUG PRINT
                print('Правильный ответ')

                # Вынимаем текущее количество правильных ответов и количество баллов пользователя
                user_result_data = QuizeResults.objects.filter(id=request.POST.get('results_object_id')).values(
                    'correct_q_num', 'score_number')

                # Увеличиваем количество правильных ответов на единицу и записыввем в базу
                QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(
                    correct_q_num=(user_result_data[0]['correct_q_num'] + 1))

                # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть
                if float(request.POST.get('q_weight')) != 0.0:
                    updated_score_number = user_result_data[0]['score_number'] + float(request.POST.get('q_weight'))

                else:
                    updated_score_number = user_result_data[0]['score_number'] + 1

                # Обновляем количетво баллов
                QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(
                    score_number=updated_score_number)
            else:
                print('Не правильный ответ')

        # Количество оставшихся у пользователя вопросов
        q_amount = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).values('q_sequence_num')

        # Номера вопросов сгенерированные пользователю
        q_num_list = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).values('questions_ids')

        # Проверяем остались ли ещё вопросы в тесте польхователя
        if int(q_amount[0]['q_sequence_num']) > 0:
            q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

            # Номер позиции вопроса в списке
            question_sequence = int(q_amount[0]['q_sequence_num']) - 1
            question_pisition = q_num_list[int(q_amount[0]['q_sequence_num']) - 1]

            # Достаём нужный вопрос из базы вопросов по сквозному номеру
            question = QuestionSet.objects.filter(id=question_pisition).values()

            # Формируем данные для отправки на страницу тестирования
            context = {'user_name': request.POST.get("user_name"), 'user_set_id': request.POST.get('user_set_id'),
                       'question': question, 'results_object_id': request.POST.get('results_object_id'),
                       'q_kind': question[0]['q_kind']}

            # Обновляем количество оставшихся вопросов
            QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).update(q_sequence_num=question_sequence)

            # Проверяем содержит ли вопрос мультивыбор
            if question[0]['q_kind'] == False:
                q_page_layout = 'start_test_radio.html'
            else:
                q_page_layout = 'start_test_check.html'

            return render(request, q_page_layout, context=context)

        else:
            # Вынимаем количество правильных ответов, число вопросов и количество баллов
            result_data = QuizeResults.objects.filter(id=int(request.POST.get('results_object_id'))).values(
                'correct_q_num', 'score_number', 'total_num_q')

            # Вынимаем количество максимально возможных баллов
            max_score_num = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).values('max_score_amount')

            # Вычисляем процент прохождения теста и округляем результат до десятой
            total_result = ('%.0f' % ((result_data[0]['score_number'] * 100) / max_score_num[0]['max_score_amount']))

            # Добавляем итоговый результать в отчёт по пользователю
            QuizeResults.objects.filter(id=int(request.POST.get('results_object_id'))).update(total_result=total_result)
            # Формируем данные для отправки
            context = {'user_name': request.POST.get("user_name"), 'total_num_q': result_data[0]['total_num_q'],
                       'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result}

            # Удаляем тест пользователя их базы
            QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).delete()

            return render(request, 'results.html', context=context)


def one_them_q(request):
    if request.method == 'POST':
        pass
    else:
        them_name = []
        for them in Thems.objects.all():
            them_name.append(them)
        context = {'thems': them_name}

        return render(request, 'one_them_q.html', context=context)


@login_required
@group_required('krs')
# Все результаты тестов
def tests_results_list(request):
    results_list = QuizeResults.objects.all()
    context = {'results': results_list}
    return render(request, 'tests_results_list.html', context=context)


@login_required
@group_required('krs')
# Детали результатов теста
def test_result_details(request, id):
    result = QuizeResults.objects.filter(id=id).values()
    context = {'result': result}
    return render(request, 'test_result_details.html', context=context)


# Список вопросов из базы
@login_required
@group_required('krs')
def question_list(request):
    result = QuestionSet.objects.all()
    context = {'questions': result}
    return render(request, 'question_list.html', context=context)


# Редактирование конкретно взятого вопроса
def question_list_details(request, id):
    #  Если пользователь нажал 'соъхранить', выполняем проверку и сохраняем форму
    if request.method == 'POST':
        #   Выясняем id вопроса для его обновления
        a = QuestionSet.objects.get(id=id)
        question_form = QuestionSetForm(request.POST, instance=a)

        if question_form.is_valid():
            question_form.save()
            return redirect('question_list')

    else:
        result = QuestionSet.objects.filter(id=id).values('them_name', 'question', 'option_1', 'option_2', 'option_3',
                                                          'option_4', 'option_5', 'q_kind', 'q_weight', 'answer',
                                                          'answers')
        question_form = QuestionSetForm(result[0])

        context = {'question_form': question_form}

        return render(request, 'question_list_details.html', context=context)


# Загрузка результата теста
def download_test_result(request, id):
    result = QuizeResults.objects.filter(id=id).values()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    # Выясняем тукущую директорию
    current_dir = os.getcwd()

    print('current_dir: ', current_dir)

    pdfmetrics.registerFont(TTFont('FreeSans', f'{current_dir}/static/FreeSans.ttf'))
    p.setFont('FreeSans', 15)

    #p.setFillColorRGB(128, 128, 128) # Цвет текста
    #p. setStrokeColorRGB(0.2, 0.5, 0.3)
    #p.setFillColorRGB(128, 128, 128)  # choose fill colour
    #p.rect(1*inch, 1*inch, 200*inch, 200*inch, fill=1)  # draw rectangle

    y = 750

    #p.line(10, 700, 400, 700 * inch)

    p.drawInlineImage(current_dir + "/static/nws_logo_white.jpg", 0, y, width=260, height=100)
    y -= 25
    p.drawString(20, y, f'ФИО: {result[0]["user_name"]}')
    y -= 25
    p.drawString(20, y, f'Дата: {result[0]["timestamp"].strftime("%d.%m.%Y %H:%M:%S")}')
    y -= 25
    p.drawString(20, y, f'Название теста: {result[0]["quize_name"]}')
    y -= 25
    p.drawString(20, y, f'Общее количество вопросов: {result[0]["total_num_q"]}')
    y -= 25
    p.drawString(20, y, f'Количество правильных ответов: {result[0]["correct_q_num"]}')
    y -= 25
    p.drawString(20, y, f'Общий результат: {result[0]["total_result"]}%')

    p.showPage()
    p.save()
    buffer.seek(0)
    filename = result[0]['user_name'].replace(' ', '')
    return FileResponse(buffer, as_attachment=True, filename=f'{filename}.pdf')
