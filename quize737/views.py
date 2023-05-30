# -*- coding: utf-8 -*-

import os
import random
import io
import csv
import re
import sys

import common
from common import send_email
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from users.models import Profile
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.forms import formset_factory, BaseFormSet
from django.templatetags.static import static
from django.core.exceptions import PermissionDenied
from django.utils import six
from django.db.models import Q
from django.shortcuts import render, redirect
from .models import QuestionSet, Thems, TestQuestionsBay, TestConstructor, QuizeSet, QuizeResults, FileUpload
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from .forms import QuestionSetForm, NewQuestionSetForm, NewTestFormName, NewTestFormQuestions, FileUploadForm, \
    NewThemeForm
from users.forms import TestsForUser
from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics  # Библиотека для формирования pdf файла
from reportlab.lib.units import inch  # Библиотека для формирования pdf файла
from reportlab.pdfbase.ttfonts import TTFont
from users.models import Profile, UserTests

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
def start(request, id=None):
    user_instance = request.user
    if request.method == 'POST':
        question_set_id = id
        test_instance = TestConstructor.objects.filter(id=question_set_id)
        q_sets_instances = TestQuestionsBay.objects.filter(test_id=question_set_id).values('theme', 'q_num')
        total_q_number = 0  # Общее количество вопросов в тесте для пользователя
        all_theme_set = []  # Объекты вопросов для пользователя
        particular_user_questions = []
        thems_num = Thems.objects.all().count()  # Общее количество тем
        max_score_number = 0  # Максимальное количество баллов по сгенерированным вопросам
        # Перебераем темы вопросов
        for q_set in q_sets_instances:
            # Перебираем темы вопросов, если тема = 5 (Все темы)
            if q_set['theme'] == 5:
                for theme in Thems.objects.all():
                    if theme.name != 'Все темы':
                        quiz_set = QuestionSet.objects.filter(them_name=theme.id)
                        quiz_set = random.sample(list(quiz_set), int(q_set['q_num']))
                        all_theme_set.append(quiz_set)
                        # Считаем количество вопросов
                        total_q_number += int(q_set['q_num'])
            # Сохраняем вопросы для пользователя в базу
            else:
                quiz_set = QuestionSet.objects.filter(them_name=q_set['theme'])
                quiz_set = random.sample(list(quiz_set), int(q_set['q_num']))
                all_theme_set.append(quiz_set)
                total_q_number += int(q_set['q_num'])
            # Добавляем номер вопроса в объект теста для пользоваетеля
        for q_set in all_theme_set:
            for q in q_set:
                particular_user_questions.append(str(q.id))
                # Если задан "вес вопроса", учитываем его в максимальном количестве баллов
                if q.q_weight != 0:
                    max_score_number = max_score_number + q.q_weight
                else:
                    max_score_number = max_score_number + 1

        total_q_num_for_user = total_q_number
        test_name = test_instance[0].name
        #  Формируем объект теста пользователя
        user_quize_set = QuizeSet.objects.create(
            test_id=test_instance[0].id,
            quize_name=test_name,
            user_under_test=user_instance.username,
            # Переводим список номеров вопросов в строку для хранения в поле базы данных
            questions_ids=' '.join(particular_user_questions),
            # Вычисляем общее количество вопросов и добавдяем их в поле
            q_sequence_num=total_q_num_for_user,
            # Вносим максимально возможное кол-во баллов
            max_score_amount=max_score_number,
            pass_score=test_instance[0].pass_score

        )

        # -------  В этом месте генерируем первый вопрос теста пользователя
        # Имя теста конкретного пользователя
        user_set_name = test_name

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
        user_name_for_h = f'{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}'
        result_obj = QuizeResults.objects.create(
            user_id=request.user,
            user_name=user_name_for_h,
            quize_name=user_set_name,
            total_num_q=sequence_number + 1,
            questions_ids=', '.join(q_num_list),
            correct_q_num=0,
            score_number=0,
            pass_score=test_instance[0].pass_score
        )

        context = {'user_name': user_instance.username, 'question': question, 'user_set_id': user_quize_set.id,
                   'results_object_id': result_obj.id, 'q_kind': question[0]['q_kind'], 'q_num_left': total_q_num_for_user}

        # Проверяем содержит ли вопрос мультивыбор
        if not question[0]['q_kind']:
            q_page_layout = 'start_test_radio.html'
        else:
            q_page_layout = 'start_test_check.html'

        return render(request, q_page_layout, context=context)

    else:
        if id:
            user_test = UserTests.objects.filter(test_name=id)
            user_tests = UserTests.objects.filter(user=request.user)
            test_instance = TestConstructor.objects.get(id=id)
            test_question_sets = TestQuestionsBay.objects.filter(test_id=id)
            context = {'question_set': test_question_sets, 'test_name': test_instance, 'user_test': user_test[0],
                       'user_tests': user_tests}
            return render(request, 'start_test_ditales.html', context=context)
        else:
            user_tests = UserTests.objects.filter(user=request.user)
            context = {'user_tests': user_tests}
            return render(request, 'start.html', context=context)


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
            user_answers_list = []
            for a in request.POST.keys():
                if 'user_answer' in a:
                    user_answers_list.append(request.POST[a][0])

            # Если ответ пользователя правильный
            if request.POST.get('answers') == ','.join(user_answers_list):

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
            # Если пользователь правильно ответил на вопрос:
            if request.POST.get('answer') == request.POST.get('user_answer'):

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

        # Проверяем остались ли ещё вопросы в тесте пользователя
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
                       'q_kind': question[0]['q_kind'], 'q_num_left': q_amount[0]['q_sequence_num']}

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
                'correct_q_num', 'score_number', 'total_num_q', 'pass_score')

            # Вынимаем количество максимально возможных баллов
            max_score_num = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).values('max_score_amount')

            # Вычисляем процент прохождения теста и округляем результат до десятой
            total_result = ('%.0f' % ((result_data[0]['score_number'] * 100) / max_score_num[0]['max_score_amount']))

            # Если пользователь сдал тест
            if int(total_result) >= int(result_data[0]['pass_score']):
                #  Вынимаем объект набора вопросов (QuizeSet) для исфользования в фильтре удаления теста польхователя, если он сдал тест
                set_instance = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id')))
                QuizeResults.objects.filter(id=int(request.POST.get('results_object_id'))).update(
                    total_result=total_result, conclusion=True)
                # Вынимаем id теста для удаления теста у пользователя
                user_test_id = set_instance[0].test_id  #  ID теста пользователя
                user_test_name = set_instance[0].quize_name  #  Название теста пользователя
                #  Удаляем тест у пользователя
                UserTests.objects.filter(user=request.user, test_name=user_test_id).delete()
                context = {'user_name': request.POST.get("user_name"), 'total_num_q': result_data[0]['total_num_q'],
                           'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result,
                           'conclusion': True}
                # Удаляем тест пользователя из базы тестов пользователя
                QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).delete()

                # Отправляем письмо КРС
                subject = f'Пилот {request.user.profile.family_name} {(request.user.profile.first_name)[0]}. {(request.user.profile.middle_name)[0]}. Сдал тест'
                message = f'Пилот {request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name} Сдал Тест: {user_test_name}\nКоличетсво набранных баллов: {total_result}%\nПроходной балл: {result_data[0]["pass_score"]}%'
                to = common.krs_mail_list
                email_msg = {'subject': subject, 'message': message, 'to': to}
                common.send_email(request, email_msg)

                return render(request, 'results.html', context=context)

            # Если пользователь тест НЕ сдал
            else:
                set_instance = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id')))
                user_test_id = set_instance[0].test_id
                user_test_name = set_instance[0].quize_name  # Название теста пользователя
                user_test_instance = UserTests.objects.filter(user=request.user, test_name=user_test_id)
                # Уменьшаем количество попыток
                num_try = user_test_instance[0].num_try
                num_try -= 1
                user_test_instance.update(num_try=num_try)
                # Если у пользователя не осталось попыток, отправляем письмо КРС
                if int(num_try) == 0:
                    subject = f'Пилот {request.user.profile.family_name} {(request.user.profile.first_name)[0]}. {(request.user.profile.middle_name)[0]}. НЕ сдал тест'
                    message = f'Пилот {request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name} НЕ сдал Тест: {user_test_name}\nКоличетсво набранных баллов: {total_result}%\nПроходной балл: {result_data[0]["pass_score"]}%\nПопыток сделано: {user_test_instance[0].num_try_initial}'
                    to = common.krs_mail_list
                    email_msg = {'subject': subject, 'message': message, 'to': to}
                    common.send_email(request, email_msg)
                # Добавляем итоговый результать в отчёт по пользователю
                # QuizeResults.objects.filter(id=int(request.POST.get('results_object_id'))).update(total_result=total_result)
                # Формируем данные для отправки
                context = {'user_name': request.POST.get("user_name"), 'total_num_q': result_data[0]['total_num_q'],
                           'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result,
                           'conclusion': False}

            # Удаляем тест пользователя из базы
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
@group_required('KRS')
# Все результаты тестов
def tests_results_list(request):
    results_list = QuizeResults.objects.all()
    paginator = Paginator(results_list, 8)
    page_number = request.GET.get('page', 1)
    results_list_pages = paginator.page(page_number)
    context = {'results': results_list_pages}
    return render(request, 'tests_results_list.html', context=context)


@login_required
@group_required('KRS')
# Детали результатов теста
def test_result_details(request, id):
    result = QuizeResults.objects.filter(id=id).values()
    context = {'result': result}
    return render(request, 'test_result_details.html', context=context)


# Список вопросов из базы
@login_required
@group_required('KRS')
def question_list(request):
    question_list = QuestionSet.objects.all()
    paginator = Paginator(question_list, 7)
    page_number = request.GET.get('page', 1)
    questions = paginator.page(page_number)
    context = {'questions': questions}
    return render(request, 'question_list.html', context=context)


# Добавить новый вопрос в базу вопросов
@login_required
@group_required('KRS')
def new_question(request):
    #  Если пользователь нажал 'сохранить', выполняем проверку и сохраняем форму
    if request.method == 'POST':
        question_form = NewQuestionSetForm(request.POST)  # Для форм основанных на модели объекта
        if question_form.is_valid():
            question_form.save()
            return redirect('quize737:question_list')
        else:
            context = {'question_form': question_form}
            return render(request, 'new_question.html', context=context)

    else:
        question_form = NewQuestionSetForm()
        context = {'question_form': question_form}
        return render(request, 'new_question.html', context=context)


# Редактирование конкретно взятого вопроса
@login_required
@group_required('KRS')
def question_list_details(request, id):
    #  Если пользователь нажал 'сохранить', выполняем проверку и сохраняем форму
    if request.method == 'POST':
        #   Выясняем id вопроса для его обновления
        a = QuestionSet.objects.get(id=id)
        question_form = QuestionSetForm(request.POST, instance=a)  # Для форм основанных на модели объекта
        if question_form.is_valid():
            question_form.save()
            return redirect('quize737:question_list')
        else:
            context = {'question_form': question_form, 'q_id': id}
            return render(request, 'question_list_details.html', context=context)

    else:
        result = QuestionSet.objects.filter(id=id).values('them_name', 'question', 'option_1', 'option_2', 'option_3',
                                                          'option_4', 'option_5', 'q_kind', 'q_weight', 'answer',
                                                          'answers', 'id')
        question_form = QuestionSetForm(result[0])

        context = {'question_form': question_form, 'q_id': result[0]['id']}

        return render(request, 'question_list_details.html', context=context)


# Удаляем вопрос
def question_del(request, id):
    QuestionSet.objects.get(id=id).delete()
    return redirect('quize737:question_list')


# Редактор тем вопросов
@login_required
@group_required('KRS')
def theme_editor(request, id=None):
    if request.method == 'POST':
        form = NewThemeForm(request.POST)
        if form.is_valid():  # TODO: добавить проверку на уже существующую тему
            theme = Thems.objects.get(id=id)
            theme.name = request.POST.get('name')
            theme.save()
            return redirect('quize737:theme_editor')
        else:
            context = {'new_theme_form': form}
            return render(request, 'edit_theme.html', context=context)
    else:
        if id:
            theme = Thems.objects.filter(id=id).values('name')
            theme_form = NewThemeForm(theme[0])
            context = {'new_theme_form': theme_form}
            return render(request, 'edit_theme.html', context=context)
        else:

            theme_list = Thems.objects.all()
            paginator = Paginator(theme_list, 7)
            page_number = request.GET.get('page', 1)
            themes = paginator.page(page_number)
            context = {'themes': themes}
            return render(request, 'theme_editor.html', context=context)


#  Создание новой темы
def new_theme(request):
    form = NewThemeForm()
    if request.method == 'POST':
        form = NewThemeForm(request.POST)
        if form.is_valid():  # TODO: добавить в валидацию проверку на уже существующую тему
            form.save()
            return redirect('quize737:theme_editor')
        else:
            context = {'new_theme_form': form}
            return render(request, 'new_theme.html', context=context)
    else:
        context = {'new_theme_form': form}
        return render(request, 'new_theme.html', context=context)


# Удаление темы
@login_required
@group_required('KRS')
def theme_del(request, id):
    Thems.objects.get(id=id).delete()
    return redirect('quize737:theme_editor')


# Скачивание результата теста
@login_required
@group_required('KRS')
def download_test_result(request, id):
    result = QuizeResults.objects.filter(id=id).values()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    # Выясняем тукущую директорию

    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    pdfmetrics.registerFont(TTFont('FreeSans', dir_path + '/static/FreeSans.ttf'))
    p.setFont('FreeSans', 15)

    # p.setFillColorRGB(128, 128, 128) # Цвет текста
    # p. setStrokeColorRGB(0.2, 0.5, 0.3)
    # p.setFillColorRGB(128, 128, 128)  # choose fill colour
    # p.rect(1*inch, 1*inch, 200*inch, 200*inch, fill=1)  # draw rectangle

    y = 750

    # p.line(10, 700, 400, 700 * inch)

    p.drawInlineImage(dir_path + '/static/nws_logo_white.jpg', 0, y, width=260, height=100)
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


# Проверка на одинаковые темы в новом тесте
class BaseArticleFormSet(BaseFormSet):

    def clean(self):
        """Checks that no two articles have the same title."""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        titles = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            title = form.cleaned_data.get("theme")
            if title in titles:
                raise ValidationError("Поля 'Тема' не могут быть одинаковыми")
            titles.append(title)


# Проверка на одинаковые названия тестов в назначенных пользователю тестах
class BaseUserTestFormSet(BaseFormSet):

    def clean(self):
        """Checks that no two articles have the same title."""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        titles = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            title = form.cleaned_data.get("test_name")
            if title in titles:
                raise ValidationError("Поля 'Название теста' не могут быть одинаковыми")
            titles.append(title)


@login_required
@group_required('KRS')
def test_editor(request):
    tests_names = TestConstructor.objects.all()
    paginator = Paginator(tests_names, 7)
    page_number = request.GET.get('page', 1)
    tests_names_pages = paginator.page(page_number)
    context = {'tests_names': tests_names_pages}
    return render(request, 'test_editor.html', context=context)


@login_required
@group_required('KRS')
def create_new_test(request):
    QuestionFormSet = formset_factory(NewTestFormQuestions, min_num=1, max_num=10, extra=0, absolute_max=20,
                                      formset=BaseArticleFormSet, can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        test_q_set = QuestionFormSet(request.POST, request.FILES, initial=[{'theme': '5', 'q_num': '4'}],
                                     prefix="questions")
        test_name_form = NewTestFormName(request.POST, prefix="test_name")

        if test_q_set.is_valid() and test_name_form.is_valid():
            # Создаём объект теста
            new_test = TestConstructor.objects.create(name=test_name_form.data['test_name-name'],
                                                      pass_score=test_name_form.data['test_name-pass_score'])
            # Создаём объекты вопросов теста
            for question in test_q_set.cleaned_data:
                TestQuestionsBay.objects.create(theme=question['theme'],
                                                test_id=new_test,
                                                q_num=question['q_num'], )
            return redirect('quize737:test_editor')
        else:
            form_errors = []  # Ошибки при валидации формы
            for error in test_q_set.errors:
                if len(error) > 0:
                    for value in error.values():
                        form_errors.append(value)
            errors_non_form = test_q_set.non_form_errors
            context = {'test_name_form': test_name_form, 'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                       'form_errors': form_errors}
            return render(request, 'new_test_form.html', context=context)
    else:
        thems = Thems.objects.all()
        total_q_num_per_them = {}
        totla_q_num = 0
        min_q_them = []
        for them_name in thems:
            # Считаем количество вопросов в каждой теме, кроме "Все темы"
            if them_name.id != 5:
                q_num = QuestionSet.objects.filter(them_name=them_name).count()
                total_q_num_per_them[f'{them_name.id}'] = q_num
                totla_q_num += 1
                min_q_them.append(q_num)
        min_q_them.sort()
        total_q_num_per_them['5'] = min_q_them[0]
        print("Q_NUM DICT:", total_q_num_per_them)
        # https://translated.turbopages.org/proxy_u/en-ru.ru.9354fe54-64555aae-631f0b43-74722d776562/https/docs.djangoproject.com/en/dev/topics/forms/formsets/#formsets
        test_name_form = NewTestFormName(prefix="test_name")
        test_q_set = QuestionFormSet(initial=[{'theme': '5', 'q_num': '4', }], prefix='questions')
        #print('form_set:', dir(test_q_set[0]))
        context = {'test_name_form': test_name_form, 'test_q_set': test_q_set, 'q_num_per_them': total_q_num_per_them}
        return render(request, 'new_test_form.html', context=context)


@login_required
@group_required('KRS')
# Редактируем Детали уже существующего конекретного теста
def test_details(request, id):
    QuestionFormSet = formset_factory(NewTestFormQuestions, min_num=1, max_num=10, extra=0, absolute_max=20,
                                      formset=BaseArticleFormSet, can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        a = TestConstructor.objects.get(id=id)
        test_name_form = NewTestFormName(request.POST)
        test_q_set = QuestionFormSet(request.POST, request.FILES, prefix="questions")
        TestQuestionsBay.objects.filter(test_id=id).delete()
        if test_q_set.is_valid():
            a.name = test_name_form.data.get('name')
            a.pass_score = test_name_form.data.get('pass_score')
            a.save()
            for question in test_q_set.cleaned_data:
                TestQuestionsBay.objects.create(theme=question['theme'],
                                                test_id=a,
                                                q_num=question['q_num'], )
            return redirect('quize737:test_editor')
        else:
            form_errors = []  # Ошибки при валидации формы
            for error in test_q_set.errors:
                if len(error) > 0:
                    for value in error.values():
                        form_errors.append(value)
            errors_non_form = test_q_set.non_form_errors
            context = {'test_name_form': test_name_form, 'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                       'form_errors': form_errors, 'test_id': id}
            return render(request, 'test_detailes.html', context=context)

    else:
        thems = Thems.objects.all()
        total_q_num_per_them = {}
        totla_q_num = 0
        min_q_them = []
        for them_name in thems:
            # Считаем количество вопросов в каждой теме, кроме "Все темы"
            if them_name.id != 5:
                q_num = QuestionSet.objects.filter(them_name=them_name).count()
                total_q_num_per_them[f'{them_name.id}'] = q_num
                totla_q_num += 1
                min_q_them.append(q_num)
        min_q_them.sort()
        total_q_num_per_them['5'] = min_q_them[0]
        result = TestConstructor.objects.filter(id=id).values('name', 'id', 'pass_score')
        test_name_form = NewTestFormName(result[0])  # Форма с названием теста
        test_questions = TestQuestionsBay.objects.filter(test_id=id).values('theme', 'q_num')
        test_q_set = QuestionFormSet(initial=test_questions, prefix='questions')
        context = {'test_q_set': test_q_set, 'test_name_form': test_name_form, 'test_id': result[0]['id'], 'q_num_per_them': total_q_num_per_them}
        return render(request, 'test_detailes.html', context=context)


# Удаляем тест
@login_required
@group_required('KRS')
def del_test(request, id):
    TestConstructor.objects.get(id=id).delete()
    return redirect('quize737:test_editor')


@login_required
@group_required('KRS')
def user_list(request):
    if request.method == 'POST':
        pass
    else:
        user_search_input = request.GET.get("user_search")
        no_search_result = False
        if user_search_input:
            user_search_data = request.GET.get("user_search").split()

            if len(user_search_data) == 3:
                total_user_list = Profile.objects.filter(Q(family_name__icontains=f'{user_search_data[0]}'), Q(first_name__icontains=f'{user_search_data[1]}'), Q(middle_name__icontains=f'{user_search_data[2]}'))
            elif len(user_search_data) == 2:
                    total_user_list = Profile.objects.filter(Q(family_name__icontains=f'{user_search_data[0]}'), Q(first_name__icontains=f'{user_search_data[1]}'))
                    if not total_user_list:
                        total_user_list = Profile.objects.filter(Q(first_name__icontains=f'{user_search_data[0]}'),
                                                                 Q(middle_name__icontains=f'{user_search_data[1]}'))

            elif len(user_search_data) == 1:
                total_user_list = Profile.objects.filter(Q(family_name__icontains=f'{user_search_data[0]}') | Q(first_name__icontains=f'{user_search_data[0]}') | Q(middle_name__icontains=f'{user_search_data[0]}'))
            else:
                no_search_result = True
                results = f'Пилоты по запросу "{user_search_input}" не найдены'
                context = {'no_search_results': no_search_result, 'results': results}
                return render(request, 'user_list.html', context=context)
            if not total_user_list:
                no_search_result = True
                results = f'Пилоты по запросу "{user_search_input}" не найдены'
                context = {'no_search_results': no_search_result, 'results': results}
                return render(request, 'user_list.html', context=context)
            else:
                paginator = Paginator(total_user_list, 20)
                page_number = request.GET.get('page', 1)
                users = paginator.page(page_number)
                context = {'user_list': users, 'no_search_results': no_search_result}
                return render(request, 'user_list.html', context=context)
        else:
            total_user_list = Profile.objects.all()
            #  Постраничная разбивка
            paginator = Paginator(total_user_list, 20)
            page_number = request.GET.get('page', 1)
            users = paginator.page(page_number)
            context = {'user_list': users, 'no_search_results': no_search_result}
            return render(request, 'user_list.html', context=context)


@login_required
@group_required('KRS')
def group_list(request):
    if request.method == 'POST':
        pass
    else:
        groups = Group.objects.all()
        paginator = Paginator(groups, 20)
        page_number = request.GET.get('page', 1)
        groups_pages = paginator.page(page_number)
        context = {'groups': groups_pages}
        return render(request, 'group_list.html', context=context)


@login_required
@group_required('KRS')
# Обрабатываем вызов деталей конкретного пользователя для назначения тестов
def user_detales(request, id):
    UserTestForm = formset_factory(TestsForUser, extra=0, formset=BaseUserTestFormSet,
                                   can_delete=True)  # Extra - количество строк формы
    user_profile = Profile.objects.filter(id=id)

    # sent = False  # Переменная для отправки письма

    if request.method == 'POST':
        tests_for_user_form = UserTestForm(request.POST, request.FILES)
        if tests_for_user_form.is_valid():
            for test in tests_for_user_form.cleaned_data:
                #  Удаляем все объекты
                # Проверяем было ли указано имя объекта
                try:
                    if UserTests.objects.get(test_name=test['test_name']):
                        UserTests.objects.filter(test_name=test['test_name']).delete()
                except Exception:
                    pass
                # Создаём только те объекты, которые не помечены для удаления
                if not test['DELETE']:
                    user = User.objects.filter(id=id)
                    UserTests.objects.create(user=user[0],
                                             test_name=test['test_name'],
                                             num_try_initial=test['num_try'],
                                             num_try=test['num_try'],
                                             date_before=test['date_before'])

                    print('USER:', user[0].profile.family_name, user[0].email)
                    #  Отправляем письмо пользователю
                    subject = f"Вам назначен Тест: '{test['test_name']}'"
                    message = f"<h4>Уважаемый, {user[0].profile.family_name} {user[0].profile.first_name} {user[0].profile.middle_name}.</h4>" \
                              f"Вам назначен тест: <b>'{test['test_name']}'</b><br>" \
                              f"На портале {config('SITE_URL', default='')}<br>" \
                              f"Тест необходимо выполнить до <b>{test['date_before'].strftime('%d.%m.%Y')}</b>"

                    email_msg = {'subject': subject, 'message': message, 'to': user[0].email}
                    send_email(request, email_msg)

            # Загружаем новые данные в форму
            user_tests = UserTests.objects.filter(user=id).values('test_name', 'num_try', 'date_before')
            tests_for_user_form = UserTestForm(initial=user_tests)
            context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form, 'test_and_data_saved': True}
            return render(request, 'user_ditales.html', context=context)

        else:
            form_errors = []  # Ошибки при валидации формы
            for error in tests_for_user_form.errors:
                if len(error) > 0:
                    for value in error.values():
                        form_errors.append(value)
            errors_non_form = tests_for_user_form.non_form_errors
            context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form,
                       'non_form_errors': errors_non_form,
                       'form_errors': form_errors, 'user_id': id}
            return render(request, 'user_ditales.html', context=context)
    else:
        user_tests = UserTests.objects.filter(user=id).values('test_name', 'num_try', 'date_before')
        tests_for_user_form = UserTestForm(initial=user_tests)
        context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form}
        return render(request, 'user_ditales.html', context=context)


@login_required
@group_required('KRS')
#  Загрузка файла с вопросами
def file_upload(request):
    upload_form = FileUploadForm()
    if request.method == 'POST':

        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            #  Зашружаем файл
            newdoc = FileUpload(docfile=request.FILES['docfile'])
            newdoc.save()
            error_read = {}  # Ошибка при чтении файл
            wrong_data = []  # Ошибки в данных файла (пропущенные поля)
            answers = ''  # Правильные ответы на вопрос
            answer = None
            them_created = 0
            questions_created = 0
            # Анализируем загруженный файл
            dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            with open(f"{dir_path}/media/documents/{request.FILES['docfile']}", newline='',
                      encoding='utf-8') as csvfile:

                #  Пропускаем первую строку (заголовок)
                heading = next(csvfile)
                fieldnames = ['theme', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'q_kind',
                              'q_weight', 'answer', 'answers']
                reader = csv.DictReader(csvfile, dialect='excel', fieldnames=fieldnames, delimiter=';')
                try:
                    for row in reader:
                        if row['theme'] and row['question'] and row['option_1'] and row['option_2'] and row['q_kind']:
                            if row['answer'] or row['answers']:
                                #  Вынимаем тему, если такой темы нет, создаём её
                                them = Thems.objects.get_or_create(name=row['theme'])
                                #  Подсчитывае созданные темы
                                if them[1]:
                                    them_created += 1
                                #  Проверяем существование вопроса, если такого вопроса нет, создаём его
                                if row['q_kind'] == 'Один Ответ':
                                    q_kind = False
                                    answer = row['answer']
                                    if len(row['answer']) > 1 or not row['answer'].isdigit():
                                        wrong_data.append(
                                            f'В поле "Ответ" должна быть одна цифра, строка {reader.line_num}')
                                        continue
                                else:
                                    q_kind = True
                                    answers = row['answers']
                                    answers = answers.replace(' ', '')
                                    if len(answers) < 2:
                                        wrong_data.append(
                                            f'В поле "Ответы" должно быть больше одной цифры и они должны быть разделены запятыми без пробелов {reader.line_num}')
                                        continue
                                if not row['q_weight']:
                                    q_weight = 0.0
                                else:
                                    q_weight = row['q_weight']
                                # проверяем наличие вопроса
                                # TODO: доделать проверку если в фале в вопросе были зменены параметры, а сам вопрос остался прежним
                                if not QuestionSet.objects.filter(question=row['question']):
                                    question = QuestionSet.objects.get_or_create(them_name=them[0],
                                                                                 question=row['question'],
                                                                                 option_1=row['option_1'],
                                                                                 option_2=row['option_2'],
                                                                                 option_3=row['option_3'],
                                                                                 option_4=row['option_4'],
                                                                                 option_5=row['option_5'],
                                                                                 q_kind=q_kind,
                                                                                 q_weight=q_weight,
                                                                                 answer=answer,
                                                                                 answers=answers
                                                                                 )
                                    if question[1]:
                                        questions_created += 1
                                else:
                                    print('Вопрос существует')
                                # Подсчитываем созданные вопросы



                            else:
                                wrong_data.append(f'Не заполненные поля в строке {reader.line_num}')
                                continue

                        else:
                            for data in row.values():
                                alpha = False
                                if data is not None:
                                    if len(data) > 2:
                                        alpha = True

                            if alpha == True:
                                wrong_data.append(f'Не заполненные поля в строке {reader.line_num}')
                                continue

                except csv.Error as e:
                    error_read = {'file': filename, 'line': reader.line_num, 'error': e}
                    sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
            os.remove(f"{dir_path}/media/documents/{request.FILES['docfile']}")

            context = {"upload_form": upload_form, 'reading_errors': error_read, 'them_num_created': them_created,
                       'q_num_created': questions_created, 'uploaded': True, 'wrong_data': wrong_data}
            return render(request, 'file_upload.html', context=context)

    else:
        context = {"upload_form": upload_form, 'uploaded': False}
        return render(request, 'file_upload.html', context=context)


# Скачивание формы для заполнения вопросов
def question_form_file_download(request):
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path_to_file = dir_path + '/static/PilotTest.xlsx'
    f = open(path_to_file, 'rb')
    return FileResponse(f, as_attachment=True, filename='PilotTest.xlsx')
