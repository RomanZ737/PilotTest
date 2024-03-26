# -*- coding: utf-8 -*-

import glob
import os
import random
import io
import csv
import re
import sys
import logging
import common

from static import text
from django.core.files.storage import FileSystemStorage
from itertools import chain
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponseRedirect
from urllib.parse import urlparse
from django.utils.encoding import force_str
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from common import send_email
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
from django.contrib.auth.models import User, Group
from users.models import Profile
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.forms import formset_factory, BaseFormSet
from django.templatetags.static import static
from django.core.exceptions import PermissionDenied
from itertools import chain

from django.db.models import Q, F
from django.shortcuts import render, redirect
from .models import QuestionSet, Thems, TestQuestionsBay, TestConstructor, QuizeSet, QuizeResults, FileUpload, \
    AnswersResults
from dbLogs.models import UserChangeLog
from django.contrib.auth.decorators import login_required, user_passes_test
import datetime
from .forms import QuestionSetForm, NewQuestionSetForm, NewTestFormName, NewTestFormQuestions, FileUploadForm, \
    NewThemeForm, MyNewTestFormQuestions, AdminMessForm, QuestionIssueMess, IMGform
from users.forms import TestsForUser, GroupForm, EditUserForm, ProfileForm, UserRegisterForm, EditGroupForm, \
    EditProfileForm
from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics  # Библиотека для формирования pdf файла
from reportlab.lib.units import inch  # Библиотека для формирования pdf файла
from reportlab.pdfbase.ttfonts import TTFont
from users.models import Profile, UserTests, GroupsDescription, TestExpired
from choices import ACTypeQ, ACTypeP, Position

from django.http import FileResponse
from reportlab.pdfgen import canvas

from common import group_required

logger_user_action = logging.getLogger('USER ACTION')
loger_pilot_answer = logging.getLogger('PILOT ANSWER')


# Заглавная страница
@login_required  # Только для зарегитсрированных пользователей
def start(request, id=None):
    try:
        user_instance = request.user
        if request.method == 'POST':
            # Проверяем, если пользователь нажал обновить страницу
            try:
                test_in_progress = QuizeSet.objects.get(test_id=id,
                                                        user_under_test=request.user.username)  # Объект сформированного пользователю теста
                user_results_instance = QuizeResults.objects.get(user_id=request.user,
                                                                 quize_name=test_in_progress.quize_name,
                                                                 in_progress=True)  # Результаты теста пользователя
                user_test = UserTests.objects.get(test_name=id,
                                                  user=user_instance)  # Объект теста конкретного пользователя
                question_set_id = id  # ID теста (сам тест), назначенного пользователю
                test_instance = TestConstructor.objects.filter(id=question_set_id)

                # Количество оставшихся у пользователя вопросов
                q_amount = test_in_progress.q_sequence_num
                q_num_list = test_in_progress.questions_ids
                q_num_list = list((q_num_list).split(' '))

                # Номер позиции вопроса в списке
                question_pisition = q_num_list[int(q_amount) - 1]

                # Достаём нужный вопрос из базы вопросов по сквозному номеру
                # question = QuestionSet.objects.filter(id=question_pisition).values()

                # Объект "следующего" вопроса
                try:
                    question_instance = QuestionSet.objects.get(id=question_pisition)
                except ObjectDoesNotExist:
                    # Если вопрос в базе не найден, генерируем случайный для конкретного типа или для всех типов
                    question_instance = QuestionSet.objects.filter(Q(ac_type=request.user.profile.ac_type)
                                                                   | Q(ac_type='ANY')).order_by('?').first()

                #  Создаём словарь с вариантами ответов на вопрос
                option_dict = {}
                for option_num in range(1, 11):
                    option_dict[f'option_{option_num}'] = getattr(question_instance, f'option_{option_num}')

                # Содержание context:
                # 'question' - Сам вопрос
                # 'tmp_test_id' - ID сформированного теста пользователю
                # 'result_id' - ID сформированных результатов теста
                # 'option_dict' - Варианты ответов на вопрос

                context = {'question': question_instance.question, 'question_id': question_instance.id,
                           'tmp_test_id': test_in_progress.id, 'result_id': user_results_instance.id,
                           'option_dict': option_dict, 'q_num_left': q_amount,
                           'q_instance': question_instance}

                # Проверяем содержит ли вопрос мультивыбор
                if not question_instance.q_kind:
                    q_page_layout = 'start_test_radio.html'
                else:
                    q_page_layout = 'start_test_check.html'

                return render(request, q_page_layout, context=context)

            except (ObjectDoesNotExist, MultipleObjectsReturned) as err:
                # Если в результате сбоя несколько результатов с ответами
                if type(err).__name__ == "MultipleObjectsReturned":
                    test_instance = TestConstructor.objects.get(id=id)  # Объект теста (изначальный, общий)
                    QuizeResults.objects.filter(user_id=request.user,
                                                quize_name=test_instance.name,
                                                in_progress=True).delete()
                    QuizeSet.objects.filter(test_id=id,
                                            user_under_test=request.user.username).delete()
                    user_test = UserTests.objects.get(test_name=id,
                                                      user=request.user)  # Объект теста назначенного пользователю
                    user_test.num_try = int(user_test.num_try) + 1
                    user_test.save()

                user_test = UserTests.objects.get(test_name=id,
                                                  user=user_instance)  # Объект теста конкретного пользователя

                #  Уменьшаем количество попыток у пользователя
                num_try = user_test.num_try  # Текущее количество попыток
                if num_try <= 0:
                    return HttpResponseRedirect('/')
                num_try -= 1
                user_test.num_try = num_try
                # user_test.update(num_try=num_try)
                user_test.save()

                question_set_id = id  # ID теста (сам тест), назначенного пользователю
                test_instance = TestConstructor.objects.filter(id=question_set_id)

                #  Вынимаем объекты Тема и Вопрос, которые принадлежат данному тесту
                q_sets_instances = TestQuestionsBay.objects.filter(test_id=question_set_id).values('theme', 'q_num')
                total_q_number = 0  # Общее количество вопросов в тесте для пользователя
                all_theme_set = []  # Объекты вопросов для пользователя
                particular_user_questions = []  # Номера вопросов в сформированном для пользователя тесте
                # thems_num = Thems.objects.all().count()  # Общее количество тем
                max_score_number = 0  # Максимальное количество баллов по сгенерированным вопросам
                # Перебераем темы вопросов
                for q_set in q_sets_instances:
                    # Перебираем темы вопросов, если тема = 5 (Все темы)
                    if q_set['theme'] == 5:
                        for theme in Thems.objects.all():
                            if theme.name != 'Все темы':
                                quiz_set = QuestionSet.objects.filter(Q(them_name=theme.name), (
                                        Q(ac_type=test_instance[0].ac_type) | Q(ac_type='ANY')), is_active=True)
                                if quiz_set.count() < int(q_set[
                                                              'q_num']):  # если в сете не оказалось достаточно вопросов по соответствующей теме, то делаем случайную выборку по недостающему числу вопросов
                                    add_num_q = int(q_set['q_num']) - quiz_set.count()
                                    add_set = QuestionSet.objects.filter(
                                        Q(ac_type=test_instance[0].ac_type) | Q(ac_type='ANY'),
                                        is_active=True).order_by('?')[:add_num_q]
                                    quiz_set = list(chain(quiz_set, add_set))  # Соединяем два QuerySet
                                quiz_set = random.sample(list(quiz_set), int(
                                    q_set['q_num']))  # Выбираем случайные вопросы, в количестве определённом в тесте
                                all_theme_set.append(quiz_set)  # Добавляем выбранные вопросы в список
                                # Считаем количество вопросов
                                total_q_number += int(q_set['q_num'])
                    # Сохраняем вопросы для пользователя в базу
                    else:

                        quiz_set = QuestionSet.objects.filter(Q(them_name=q_set['theme']),
                                                              (Q(ac_type=test_instance[0].ac_type) | Q(ac_type='ANY')),
                                                              is_active=True)
                        if quiz_set.count() < int(q_set[
                                                      'q_num']):  # если в сете не оказалось достаточно вопросов по соответствующей теме, (например после формирования теста в конструкторе тесто база вопросов подверглась редактированию)то делаем случайную выборку по недостающему числу вопросов

                            add_num_q = int(q_set['q_num']) - quiz_set.count()

                            add_set = QuestionSet.objects.filter(Q(ac_type=test_instance[0].ac_type) | Q(ac_type='ANY'),
                                                                 is_active=True).order_by('?')[:add_num_q]

                            quiz_set = list(chain(quiz_set, add_set))  # Соединяем два QuerySet
                        quiz_set = random.sample(list(quiz_set), int(q_set['q_num']))
                        all_theme_set.append(quiz_set)
                        total_q_number += int(q_set['q_num'])
                    # Добавляем номер вопроса в объект теста для пользоваетеля
                for q_set in all_theme_set:
                    for q in q_set:
                        particular_user_questions.append(str(q.id))
                        # Если задан "вес вопроса", учитываем его в максимальном количестве баллов
                        if q.q_weight != 0.0:
                            max_score_number = max_score_number + q.q_weight
                        else:
                            max_score_number = max_score_number + 1.0

                test_name = test_instance[0].name
                #  Формируем объект теста пользователя (создаётся на время теста)
                user_quize_set = QuizeSet.objects.create(  # Объект сформированного теста для пользователя
                    test_id=test_instance[0].id,  # ID теста, назначенного пользователю
                    quize_name=test_name,  # Название теста
                    user_under_test=user_instance.username,  # Логин (уникальный) пользователя проходящего тест
                    # Переводим список номеров вопросов в строку для хранения в поле базы данных
                    questions_ids=' '.join(particular_user_questions),
                    # Номера вопросов в сформированном для пользоваетля тесте
                    q_sequence_num=total_q_number,  # Общее количество вопросов
                    max_score_amount=max_score_number,  # Масимальное количество баллов по тесту
                    pass_score=test_instance[0].pass_score  # Минимальный проходной бал по тесту
                )

                # -------  В этом месте генерируем первый вопрос теста пользователя

                # Достаём из базы вопросов первый вопрос с конца
                sequence_number = (total_q_number - 1)  # Номер вопроса в списке вопросов пользователя
                question_pisition = particular_user_questions[
                    sequence_number]  # Номер вопроса в списке вопросов пользователя

                # Достаём нужный вопрос из базы вопросов по сквозному номеру
                # question = QuestionSet.objects.filter(id=question_pisition).values()
                # Вынимаем объект вопроса
                try:
                    question_instance = QuestionSet.objects.get(id=question_pisition)
                except ObjectDoesNotExist:
                    # Если вопрос в базе не найден, генерируем случайный для конкретного типа или для всех типов
                    question_instance = QuestionSet.objects.filter(Q(ac_type=request.user.profile.ac_type)
                                                                   | Q(ac_type='ANY')).order_by('?').first()

                # Формируем данные для отправки на страницу тестирования

                # Обновляем количество оставшихся вопросов - закоментил т.е. уменьшать количество вопросов надо после ответа пользователя
                # QuizeSet.objects.filter(id=user_quize_set.id).update(q_sequence_num=sequence_number)
                # Создаём запись с результатами теста
                user_name_for_h = f'{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}'
                result_obj = QuizeResults.objects.create(
                    user_id=request.user,
                    user_name=user_name_for_h,
                    quize_name=test_name,
                    total_num_q=sequence_number + 1,
                    questions_ids=', '.join(particular_user_questions),
                    correct_q_num=0,
                    score_number=0,
                    pass_score=test_instance[0].pass_score,
                    total_num_try=user_test.num_try_initial,
                    try_spent=user_test.num_try_initial - user_test.num_try
                )

                # Прописываем ID результатов выполнения теста в тест пользователя, что бы привязаться к конкретной попытке.
                user_test.results_id = result_obj.id
                user_test.save()
                #  Создаём словарь с вариантами ответов на вопрос
                option_dict = {}
                for option_num in range(1, 11):
                    option_dict[f'option_{option_num}'] = getattr(question_instance, f'option_{option_num}')

                # Содержание context:
                # 'question' - Сам вопрос
                # 'tmp_test_id' - ID сформированного теста пользователю
                # 'result_id' - ID сформированных результатов теста
                # 'option_dict' - Варианты ответов на вопрос

                context = {'question': question_instance.question, 'question_id': question_instance.id,
                           'tmp_test_id': user_quize_set.id, 'result_id': result_obj.id, 'option_dict': option_dict,
                           'q_num_left': total_q_number, 'q_instance': question_instance}
                # Проверяем содержит ли вопрос мультивыбор
                if not question_instance.q_kind:
                    q_page_layout = 'start_test_radio.html'
                else:
                    q_page_layout = 'start_test_check.html'

                return render(request, q_page_layout, context=context)
        # Если пользователь открывает страницу
        else:
            # Если пользователь выбирает конкретный тест из списка назначенных
            if id:
                #  Проверяем, есть ли у пользователя не завершённые тесты
                try:
                    test_in_progress = QuizeSet.objects.get(test_id=id,
                                                            user_under_test=request.user.username)  # Объект сформированного пользователю теста (когда пользователь нажимает кнопку "Начать тестирование")
                    #  Если сформированный пользователю тест существует, продолжаем выполнение
                    q_num_left = test_in_progress.q_sequence_num
                    in_progress = True  # Флаг не завершённого теста
                    test_instance = TestConstructor.objects.get(id=id)  # Объект теста (изначальный, общий)
                    user_test = UserTests.objects.filter(test_name=id,
                                                         user=request.user)  # Объект теста назначенного пользователю
                    test_mess_for_user = user_test.test_name.for_user_comment #  Вынимаем сообщение для пользователя
                    results_instance = QuizeResults.objects.get(user_id=request.user,
                                                                quize_name=test_instance.name,
                                                                in_progress=True)  # Сформированный результат выполнения теста

                    user_tests = UserTests.objects.filter(
                        user=request.user)  # Весь список тестов пользователя для отображения в боковом меню
                    test_question_sets = TestQuestionsBay.objects.filter(
                        test_id=id)  # Вопросы теста, назначенного пользователю
                    user_mess = text.USER_MESSAGE_BEFORE_TEST

                    context = {'question_set': test_question_sets, 'test_name': test_instance,
                               'user_test': user_test[0],
                               'user_tests': user_tests, 'in_progress': in_progress,
                               'tmp_test_id': test_in_progress.id,
                               'result_id': results_instance.id, 'question_id': id,
                               'q_num_left': q_num_left, 'user_mess': user_mess, 'for_user_comment': test_mess_for_user}
                    return render(request, 'start_test_ditales.html', context=context)

                except (ObjectDoesNotExist, MultipleObjectsReturned) as err:
                    user_mess = text.USER_MESSAGE_BEFORE_TEST
                    if err == MultipleObjectsReturned:
                        test_instance = TestConstructor.objects.get(id=id)  # Объект теста (изначальный, общий)
                        QuizeResults.objects.filter(user_id=request.user,
                                                    quize_name=test_instance.name,
                                                    in_progress=True).delete()
                        QuizeSet.objects.get(test_id=id,
                                             user_under_test=request.user.username).delete()
                        user_test = UserTests.objects.filter(test_name=id,
                                                             user=request.user)  # Объект теста назначенного пользователю
                        user_test.num_try = int(user_test.num_try) + 1
                        user_test.save()

                    in_progress = False
                    user_test = UserTests.objects.filter(test_name=id, user=request.user)  # Выбраный пользователем тест
                    user_tests = UserTests.objects.filter(
                        user=request.user)  # Весь список тестов пользователя для отображения
                    test_instance = TestConstructor.objects.get(id=id)
                    test_question_sets = TestQuestionsBay.objects.filter(test_id=id)
                    context = {'question_set': test_question_sets, 'test_name': test_instance,
                               'user_test': user_test[0],
                               'user_tests': user_tests,
                               'in_progress': in_progress, 'user_mess': user_mess,
                               'for_user_comment': test_instance.for_user_comment}
                    return render(request, 'start_test_ditales.html', context=context)



            #  Если пользователь открывает страницу со списком тестов
            else:
                # проверяем есть ли у пользователя не завершённые тесты
                tests_in_prog = []

                tests_objects_in_progress = QuizeSet.objects.filter(
                    user_under_test=request.user.username)  # Объект сформированного пользователю теста (когда пользователь нажимает кнопку "Начать тестирование")
                for id in tests_objects_in_progress:
                    tests_in_prog.append(id.test_id)
                # Проверяем просроченные тесты по дате
                # test_date_expire = UserTests.objects.filter(date_before__lt=datetime.date.today())
                # Проверяем просроченные тесты по кол-ву попыток
                # test_num_try_expire = UserTests.objects.filter(num_try__lte=0)
                # test_num_try_expire = test_num_try_expire.filter(user__quizeresults__in_progress=False)
                # total_expired_user_tests = UserTests.objects.filter(Q(num_try__lte=0)).order_by('date_before').distinct()
                # total_expired_user_tests = list(chain(test_date_expire, test_num_try_expire))

                total_expired_user_tests = (UserTests.objects.filter((Q(num_try__lte=0) &
                                                                      Q(user__quizeresults__in_progress=False) &
                                                                      Q(results_id=F('user__quizeresults__id'))) |
                                                                     Q(date_before__lt=datetime.date.today()))
                                            .order_by('date_before').distinct())
                user_tests = UserTests.objects.filter(user=request.user)
                context = {'user_tests': user_tests, 'tests_in_prog': tests_in_prog,
                           'expired_tests': total_expired_user_tests}
                return render(request, 'start.html', context=context)
    except Exception as general_error:
        # Формируем письмо администратору
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        contence_of_mess = f'File:\n' \
                           f'{filename}\n' \
                           f'<b>Номер строки:</b> {line_number}\n\n' \
                           f'Вероятно пользователь обновил страницу с результатами теста'
        to = common.admin_email
        subject = f'!Серверная ошибка! Pilot Test'
        message = f'<p style="font-size: 20px;">Пользователь:</p>' \
                  f'<span style="font-size: 18px;"><b>{request.user.profile.position} </b></span>' \
                  f'<span style="font-size: 18px;"><b>{request.user.profile.ac_type}</b></span>' \
                  f'<p style="font-size: 18px;"><b>{request.user.profile.family_name} {request.user.profile.first_name}' \
                  f' {request.user.profile.middle_name}</b></p><br>' \
                  f'<p style="font-size: 20px;"><b>Текст ошибки:</b></p>' \
                  f'<p style="font-size: 18px;">{general_error}</p>' \
                  f'<p style="font-size: 20px;"><b>Сообщение:</b></p>' \
                  f'<p style="font-size: 18px;">{contence_of_mess}</p><br>' \
                  f'<a href="mailto:{request.user.email}">Ответить</a>'
        email_msg = {'subject': subject, 'message': message, 'to': to}
        common.send_email(request, email_msg)
        # Отправляем пользователя на заглавную страницу
        return HttpResponseRedirect('/')


@login_required  # Только для зарегитсрированных пользователей
# Генерация последующих вопросов
def next_question(request):
    try:
        if request.method == 'POST':
            #  Если пользователь продолжает попытку
            if 'continue_test' in request.POST.keys():
                user_quize_set_id = int(request.POST.get(
                    'tmp_test_id'))  # ID сформированного пользователю теста, удаляется после завершения теста пользователем (с любым результатом)
                # Количество оставшихся у пользователя вопросов
                q_amount = QuizeSet.objects.filter(id=user_quize_set_id).values('q_sequence_num')
                q_num_list = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values('questions_ids')
                q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

                # Номер позиции вопроса в списке
                question_pisition = q_num_list[int(q_amount[0]['q_sequence_num']) - 1]

                # Достаём нужный вопрос из базы вопросов по сквозному номеру
                question = QuestionSet.objects.filter(id=question_pisition).values()

                # Объект "следующего" вопроса
                question_instance = QuestionSet.objects.get(id=question_pisition)

                #  Создаём словарь с вариантами ответов на вопрос
                option_dict = {}
                for option_num in range(1, 11):
                    option_dict[f'option_{option_num}'] = question[0][f'option_{option_num}']

                # Содержание context:
                # 'question' - Сам вопрос
                # 'tmp_test_id' - ID сформированного теста пользователю
                # 'result_id' - ID сформированных результатов теста
                # 'option_dict' - Варианты ответов на вопрос

                context = {'question': question[0]['question'], 'question_id': question[0]['id'],
                           'tmp_test_id': request.POST.get('tmp_test_id'), 'result_id': request.POST.get('result_id'),
                           'option_dict': option_dict, 'q_num_left': q_amount[0]['q_sequence_num'],
                           'q_instance': question_instance}

                # Проверяем содержит ли вопрос мультивыбор
                if question[0]['q_kind'] == False:
                    q_page_layout = 'start_test_radio.html'
                else:
                    q_page_layout = 'start_test_check.html'

                return render(request, q_page_layout, context=context)
            # Если пользователь нажал кнопку ответить или обновил страницу
            else:

                #  Вынимает объект результатов пользователя
                results_inst = QuizeResults.objects.get(id=request.POST.get('result_id'))
                #  Вынимаем объект отвеченного вопроса
                answered_q_instance = QuestionSet.objects.get(id=request.POST.get('question_id'))
                # Проверяем нажал пользователь кнопку обновить или кнопку "Ответить"
                try:
                    answer_result = AnswersResults.objects.get(results=results_inst, question=answered_q_instance)

                    # ID сформированного пользователю теста, удаляется после завершения теста пользователем (с любым результатом)
                    user_quize_set_id = int(request.POST.get('tmp_test_id'))
                    # Количество оставшихся у пользователя вопросов
                    q_amount = QuizeSet.objects.filter(id=user_quize_set_id).values('q_sequence_num')
                    q_num_list = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values(
                        'questions_ids')
                    q_num_list = list((q_num_list[0]['questions_ids']).split(' '))
                    # Номер позиции вопроса в списке
                    question_pisition = q_num_list[int(q_amount[0]['q_sequence_num']) - 1]
                    # Достаём нужный вопрос из базы вопросов по сквозному номеру
                    # question = QuestionSet.objects.filter(id=question_pisition).values()
                    # Объект "следующего" вопроса
                    try:
                        question_instance = QuestionSet.objects.get(id=question_pisition)
                    except ObjectDoesNotExist:
                        # Если вопрос в базе не найден, генерируем случайный для конкретного типа или для всех типов
                        question_instance = QuestionSet.objects.filter(Q(ac_type=request.user.profile.ac_type)
                                                                       | Q(ac_type='ANY')).order_by('?').first()
                    #  Создаём словарь с вариантами ответов на вопрос
                    option_dict = {}
                    for option_num in range(1, 11):
                        option_dict[f'option_{option_num}'] = getattr(question_instance, f'option_{option_num}')
                    # Содержание context:
                    # 'question' - Сам вопрос
                    # 'tmp_test_id' - ID сформированного теста пользователю
                    # 'result_id' - ID сформированных результатов теста
                    # 'option_dict' - Варианты ответов на вопрос
                    context = {'question': question_instance.question, 'question_id': question_instance.id,
                               'tmp_test_id': request.POST.get('tmp_test_id'),
                               'result_id': request.POST.get('result_id'),
                               'option_dict': option_dict, 'q_num_left': q_amount[0]['q_sequence_num'],
                               'q_instance': question_instance}
                    # Проверяем содержит ли вопрос мультивыбор
                    if not question_instance.q_kind:
                        q_page_layout = 'start_test_radio.html'
                    else:
                        q_page_layout = 'start_test_check.html'
                    return render(request, q_page_layout, context=context)

                #  Если пользователь нажал кнопку ответить
                except ObjectDoesNotExist:
                    user_quize_set_id = int(request.POST.get(
                        'tmp_test_id'))  # ID сформированного пользователю теста, удаляется после завершения теста пользователем (с любым результатом)
                    # Количество оставшихся у пользователя вопросов
                    q_amount = QuizeSet.objects.filter(id=user_quize_set_id).values('q_sequence_num')
                    # Уменьшаем на единицу количество оставшихся вопросов
                    question_sequence = int(q_amount[0]['q_sequence_num']) - 1
                    # Обновляем количество оставшихся вопросов
                    QuizeSet.objects.filter(id=user_quize_set_id).update(q_sequence_num=question_sequence)
                    # Проверяем вид вопроса
                    #  Если вопрос имеет несколько вариантов ответа
                    if answered_q_instance.q_kind:
                        # Преобразуем ответы пользователя во множество
                        user_answers_set = set()
                        for answer in request.POST.getlist('user_answer'):
                            user_answers_set.add(int(answer.replace('option_', '')))
                        # Вынимаем правильные ответы из вопроса и преобразуем во множество чисел
                        correct_answers_set = set(map(int, (answered_q_instance.answers).split(',')))

                        # Формируем список ответов для лога
                        def get_answers(answers_):
                            text = ''
                            for a in answers_:
                                text = text + getattr(answered_q_instance, f'option_{a}') + "\n"
                            return text

                        # Если ответ пользователя правильный
                        if user_answers_set == correct_answers_set:
                            #  Создаём объект ответа на вопрос конкретного теста
                            AnswersResults.objects.create(user=request.user,
                                                          results=results_inst,
                                                          question=answered_q_instance,
                                                          user_answer=user_answers_set,
                                                          conclusion=True
                                                          )
                            loger_pilot_answer.info(f"{request.user.username}; "
                                                    f">>PASS<<;{request.user.profile.family_name};"
                                                    f" {request.user.profile.first_name[0]}."
                                                    f"{request.user.profile.middle_name[0]}.;"
                                                    f"Question(ID:{answered_q_instance.id}):;"
                                                    f"{answered_q_instance.question};"
                                                    f"Pilot Answers:{get_answers(user_answers_set)};"
                                                    f"Correct Answers:{get_answers(correct_answers_set)};")
                            # Вынимаем текущее количество правильных ответов и количество баллов пользователя
                            user_result_data = QuizeResults.objects.filter(id=request.POST.get('result_id')).values(
                                'correct_q_num', 'score_number')

                            # Увеличиваем количество правильных ответов на единицу и записыввем в базу
                            QuizeResults.objects.filter(id=request.POST.get('result_id')).update(
                                correct_q_num=(user_result_data[0]['correct_q_num'] + 1))

                            # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть

                            if answered_q_instance.q_weight != 0:
                                updated_score_number = user_result_data[0][
                                                           'score_number'] + answered_q_instance.q_weight
                            else:
                                updated_score_number = user_result_data[0]['score_number'] + 1

                            # Обновляем количетво баллов
                            QuizeResults.objects.filter(id=request.POST.get('result_id')).update(
                                score_number=updated_score_number)

                        #  Создаём объект ответа на вопрос конкретного теста
                        else:
                            AnswersResults.objects.create(user=request.user,
                                                          results=results_inst,
                                                          question=answered_q_instance,
                                                          user_answer=user_answers_set,
                                                          conclusion=False
                                                          )

                            loger_pilot_answer.info(f"{request.user.username};"
                                                    f">>FAIL<<;{request.user.profile.family_name}"
                                                    f" {request.user.profile.first_name[0]}."
                                                    f"{request.user.profile.middle_name[0]}.;"
                                                    f"Question(ID:{answered_q_instance.id}):;"
                                                    f"{answered_q_instance.question};"
                                                    f"Pilot Answers:{get_answers(user_answers_set)};"
                                                    f"Correct Answers:{get_answers(correct_answers_set)};")
                    else:
                        #  Если вопрос с одним вариантом ответа
                        user_aswer = request.POST.get('user_answer').replace('option_', '')
                        full_user_answer = getattr(answered_q_instance, request.POST.get('user_answer'))
                        full_correct_answer = getattr(answered_q_instance, f'option_{answered_q_instance.answer}')
                        # Если пользователь правильно ответил на вопрос:
                        if int(answered_q_instance.answer) == int(user_aswer):
                            #  Создаём объект ответа на вопрос конкретного теста
                            AnswersResults.objects.create(user=request.user,
                                                          results=results_inst,
                                                          question=answered_q_instance,
                                                          user_answer=user_aswer,
                                                          conclusion=True
                                                          )
                            loger_pilot_answer.info(f"{request.user.username};"
                                                    f">>PASS<<;{request.user.profile.family_name}"
                                                    f" {request.user.profile.first_name[0]}."
                                                    f"{request.user.profile.middle_name[0]}.;"
                                                    f"Question(ID:{answered_q_instance.id}):;"
                                                    f"{answered_q_instance.question};"
                                                    f"Pilot Answer:{full_user_answer};"
                                                    f"Correct Answer:{full_correct_answer};")
                            # Вынимаем текущее количество правильных ответов и количество баллов пользователя
                            user_result_data = QuizeResults.objects.filter(id=request.POST.get('result_id')).values(
                                'correct_q_num', 'score_number')

                            # Увеличиваем количество правильных ответов на единицу и записыввем в базу
                            QuizeResults.objects.filter(id=request.POST.get('result_id')).update(
                                correct_q_num=(user_result_data[0]['correct_q_num'] + 1))

                            # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть

                            if float(answered_q_instance.q_weight) != 0:
                                updated_score_number = user_result_data[0]['score_number'] + float(
                                    answered_q_instance.q_weight)

                            else:
                                updated_score_number = user_result_data[0]['score_number'] + 1

                            # Обновляем количетво баллов
                            QuizeResults.objects.filter(id=request.POST.get('result_id')).update(
                                score_number=updated_score_number)
                        else:
                            #  Создаём объект ответа на вопрос конкретного теста
                            AnswersResults.objects.create(user=request.user,
                                                          results=results_inst,
                                                          question=answered_q_instance,
                                                          user_answer=user_aswer,
                                                          conclusion=False
                                                          )

                            loger_pilot_answer.info(f"{request.user.username};"
                                                    f">>FAIL<<;{request.user.profile.family_name}"
                                                    f" {request.user.profile.first_name[0]}."
                                                    f"{request.user.profile.middle_name[0]}.;"
                                                    f"Question(ID:{answered_q_instance.id}):;"
                                                    f"{answered_q_instance.question};"
                                                    f"Pilot Answer:{full_user_answer};"
                                                    f"Correct Answer:{full_correct_answer};")
                    # # Количество оставшихся у пользователя вопросов
                    # q_amount = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values('q_sequence_num')

                    # Номера вопросов сгенерированные пользователю
                    q_num_list = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values(
                        'questions_ids')

                    # Проверяем остались ли ещё вопросы в тесте пользователя
                    if int(q_amount[0]['q_sequence_num']) > 0:
                        q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

                        # Номер позиции вопроса в списке
                        # question_sequence = int(q_amount[0]['q_sequence_num']) - 1
                        question_id = q_num_list[int(q_amount[0]['q_sequence_num']) - 1]

                        # Достаём нужный вопрос из базы вопросов по сквозному номеру
                        # question = QuestionSet.objects.filter(id=question_id).values()

                        # Объект "следующего" вопроса
                        try:
                            question_instance = QuestionSet.objects.get(id=question_id)
                        except ObjectDoesNotExist:
                            # Если вопрос в базе не найден, генерируем случайный для конкретного типа или для всех типов
                            question_instance = QuestionSet.objects.filter(Q(ac_type=request.user.profile.ac_type)
                                                                           | Q(ac_type='ANY')).order_by('?').first()

                        #  Создаём словарь с вариантами ответов на вопрос
                        option_dict = {}
                        # for option_num in range(1, 11):
                        #     option_dict[f'option_{option_num}'] = question[0][f'option_{option_num}']

                        for option_num in range(1, 11):
                            option_dict[f'option_{option_num}'] = getattr(question_instance, f'option_{option_num}')

                        # Содержание context:
                        # 'question' - Сам вопрос
                        # 'tmp_test_id' - ID сформированного теста пользователю
                        # 'result_id' - ID сформированных результатов теста
                        # 'option_dict' - Варианты ответов на вопрос

                        # context = {'question': question[0]['question'], 'question_id': question[0]['id'],
                        #            'tmp_test_id': request.POST.get('tmp_test_id'),
                        #            'result_id': request.POST.get('result_id'),
                        #            'option_dict': option_dict, 'q_num_left': q_amount[0]['q_sequence_num'],
                        #            'q_instance': question_instance}

                        context = {'question': question_instance.question, 'question_id': question_instance.id,
                                   'tmp_test_id': request.POST.get('tmp_test_id'),
                                   'result_id': request.POST.get('result_id'),
                                   'option_dict': option_dict, 'q_num_left': q_amount[0]['q_sequence_num'],
                                   'q_instance': question_instance}

                        # Формируем данные для отправки на страницу тестирования
                        # context = {'user_name': request.POST.get("user_name"), 'user_set_id': request.POST.get('user_set_id'), 'question': question, 'results_object_id': request.POST.get('results_object_id'), 'q_kind': question[0]['q_kind'], 'q_num_left': q_amount[0]['q_sequence_num']}

                        # Обновляем количество оставшихся вопросов
                        QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).update(
                            q_sequence_num=question_sequence)

                        # Проверяем содержит ли вопрос мультивыбор
                        if not question_instance.q_kind:
                            q_page_layout = 'start_test_radio.html'
                        else:
                            q_page_layout = 'start_test_check.html'

                        return render(request, q_page_layout, context=context)

                    else:
                        context = {}
                        conclusion = ''
                        #  Вынимаем объект результатов теста
                        results_instance = QuizeResults.objects.get(id=int(request.POST.get('result_id')))

                        #  Вынисмаем объект сформированно "на сеанс" теста (когда пользователь нажимает кнопку "начать тестирования")
                        quiz_set_instance = QuizeSet.objects.get(id=int(request.POST.get('tmp_test_id')))

                        #  Вынимаем объект теста, назначенного конкретному пользователю
                        user_test_instance = UserTests.objects.get(user=request.user,
                                                                   test_name=quiz_set_instance.test_id)
                        #  Вынимаем объект оригинального теста
                        original_test_inst = TestConstructor.objects.get(pk=user_test_instance.test_name.id)
                        # Вынимаем количество максимально возможных баллов
                        max_score_num = float(quiz_set_instance.max_score_amount)
                        # Вынимаем количество набранных баллов
                        score_number = float(results_instance.score_number)
                        # Вынимает минимальный процент необходимый для прохождения теста
                        min_pass_score = int(results_instance.pass_score)
                        #  Вынимаем флаг теста (теринровка или нет)
                        test_flag = user_test_instance.test_name.training
                        #  Вынимаем Название теста пользователя
                        user_test_name = quiz_set_instance.quize_name

                        # Вычисляем процент прохождения теста и округляем результат до десятой
                        total_result = int(('%.0f' % ((score_number * 100) / max_score_num)))

                        # Ставим флаг завершённости теста
                        results_instance.in_progress = False
                        #  Записываем в отчёт о тесте: результат сдачи,
                        results_instance.total_result = total_result
                        #  Выясняем нужно ли выставлять оценку пользователю
                        if original_test_inst.set_mark:
                            #  Вынимаем максимум процентов для тройки
                            max_three = original_test_inst.mark_four
                            #  Вынимаем максимум процентов для четвёрки
                            max_four = original_test_inst.mark_five
                            if total_result < min_pass_score:
                                results_instance.total_mark = 2
                            elif min_pass_score <= total_result <= max_three:
                                results_instance.total_mark = 3
                            elif max_three < total_result <= max_four:
                                results_instance.total_mark = 4
                            else:
                                results_instance.total_mark = 5
                            results_instance.mark_four = max_three
                            results_instance.mark_five = max_four
                        #  Сохраняем данные
                        results_instance.save()

                        #  Формируем данные для отображения
                        user_name = results_instance.user_name  # Имя пользователя для отображения
                        total_num_q = results_instance.total_num_q  # Общее количество ответов
                        correct_q_num = results_instance.correct_q_num  # Количество правильных ответов
                        quize_name = results_instance.quize_name
                        ac_type = results_instance.user_id.profile.get_ac_type_display
                        timestamp = results_instance.timestamp
                        total_mark = results_instance.total_mark

                        #  Формируем результаты ответов на тест
                        answer_results = []
                        answers = AnswersResults.objects.filter(user=results_inst.user_id, results=results_inst)
                        #  Формируем список ответов в результатах теста
                        for question in answers:
                            question_block = {}
                            question_block['id'] = question.question.id
                            question_block['comment_img'] = question.question.comment_img
                            question_block['comment_text'] = question.question.comment_text
                            question_block['question'] = question.question.question
                            question_block['conclusion'] = question.conclusion
                            #  Если вопрос имеет один ответ
                            if not question.question.q_kind:
                                options = []
                                for i in range(1, 11):
                                    if question.question.answer == i:
                                        options.append(
                                            {f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                                    else:
                                        if getattr(question.question, f'option_{i}'):
                                            options.append(
                                                {f'option': getattr(question.question, f'option_{i}'),
                                                 'valid': False})
                                user_answer = question.user_answer
                                question_block['answers'] = options
                                question_block['user_answer'] = [
                                    getattr(question.question, f'option_{user_answer}')]

                            #  Если на вопрос несколько ответов
                            else:
                                options = []
                                #  Список с правильными ответами
                                correct_answers_list = list(map(int, question.question.answers.split(',')))

                                for i in range(1, 11):
                                    if i in correct_answers_list:
                                        options.append(
                                            {f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                                    else:
                                        if getattr(question.question, f'option_{i}'):
                                            options.append(
                                                {f'option': getattr(question.question, f'option_{i}'),
                                                 'valid': False})

                                question_block['answers'] = options
                                user_answers = []
                                for number in question.user_answer:
                                    if number.isdigit():
                                        user_answers.append(number)
                                answer = []
                                for user_answer in user_answers:
                                    answer.append(getattr(question.question, f'option_{user_answer}'))
                                question_block['user_answer'] = answer

                            answer_results.append(question_block)

                        # Если пользователь сдал тест
                        if total_result >= min_pass_score:
                            conclusion = True
                            #  Записываем в отчёт о тесте заключение
                            results_instance.conclusion = conclusion
                            results_instance.date_end = datetime.datetime.utcnow()
                            #  Сохраняем данные
                            results_instance.save()

                            # Отправляем письмо КРС если тест не тренировочный
                            if not test_flag:
                                site_url = config('SITE_URL', default='')
                                subject = f'Пилот {request.user.profile.family_name} {(request.user.profile.first_name)[0]}. {(request.user.profile.middle_name)[0]}. Сдал Тест'
                                message = f'<p style="font-size: 20px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
                                          f'<p style="color: rgb(148, 192, 74); font-size: 20px;"><b>СДАЛ ТЕСТ</b></p>' \
                                          f'<p style="font-size: 15px;">Название теста: <b>{user_test_name}</b></p>' \
                                          f'<p style="font-size: 15px;">Набрано баллов: <b>{total_result}%</b></p>' \
                                          f'<p style="font-size: 15px;">Проходной балл: <b>{min_pass_score}%</b></p>' \
                                          f'<a href="{site_url}/tests_results_list/{results_instance.id}">Посмотреть подробности</a>' \
                                          f'<br>' \
                                          f'<br>' \
                                          f'<a href="{site_url}/download_test_result/{results_instance.id}">Скачать результаты теста</a>'
                                # Вынимаем список адресов КРС соответствующих данному тесту
                                email_list = user_test_instance.test_name.email_to_send.split()

                                email_msg = {'subject': subject, 'message': message, 'to': email_list}
                                common.send_email(request, email_msg)

                            else:  # Если тест тренировочный, удаляем результаты теста
                                results_instance.delete()

                            #  Удаляем тест у пользователя т.к. он его сдал успешно
                            user_test_instance.delete()
                            # Удаляем сгенерированный тест (был сформирован когда пользователь нажал кнопку "Начать
                            # тестирование") т.к. это временный объект, в любом случае удаляется после полного
                            # завершения теста
                            quiz_set_instance.delete()

                        # Если пользователь тест НЕ сдал
                        else:
                            #  Записываем в отчёт о тесте заключение
                            conclusion = False
                            results_instance.conclusion = conclusion
                            results_instance.date_end = datetime.datetime.utcnow()
                            #  Сохраняем данные
                            results_instance.save()
                            # Вынимаем количество оставшихся попыток
                            num_try = user_test_instance.num_try
                            # Если у пользователя не осталось попыток, отправляем письмо КРС, если тест НЕ тренировочный
                            if int(num_try) <= 0:
                                # Отправляем письмо КРС если тест не тренировочный
                                if not test_flag:
                                    site_url = config('SITE_URL', default='')
                                    subject = f'Пилот {request.user.profile.family_name} {(request.user.profile.first_name)[0]}. {(request.user.profile.middle_name)[0]}. НЕ сдал тест'
                                    message = f'<p style="font-size: 20px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
                                              f'<p style="color: rgb(142, 23, 11); font-size: 20px;"><b>НЕ СДАЛ ТЕСТ</b></p>' \
                                              f'<p style="font-size: 15px;">Название теста: <b>{user_test_name}</b></p>' \
                                              f'<p style="font-size: 15px;">Набрано баллов: <b>{total_result}%</b></p>' \
                                              f'<p style="font-size: 15px;">Проходной балл: <b>{min_pass_score}%</b></p>' \
                                              f'<a href="{site_url}/tests_results_list/{results_instance.id}">' \
                                              f'<span style="font-size: 14px;">Посмотреть подробности</span></a>' \
                                              f'<br>' \
                                              f'<br>' \
                                              f'<a href="{site_url}/user_list/{request.user.id}">' \
                                              f'<span style="font-size: 14px;">Добавить попытки прохождения</span></a>' \
                                              f'<br>' \
                                              f'<br>' \
                                              f'<a href="{site_url}/download_test_result/{results_instance.id}">' \
                                              f'<span style="font-size: 14px;">Скачать результаты теста</span></a>'
                                    # Вынимаем список адресов КРС соответствующих данному тесту
                                    email_list = (user_test_instance.test_name.email_to_send).split()
                                    email_msg = {'subject': subject, 'message': message, 'to': email_list}
                                    common.send_email(request, email_msg)

                                else:  # Удаляем результаты теста, если тест тренировочный
                                    results_instance.delete()

                                # Удаляем сгенерированный тест (был сформирован когда пользователь нажал кнопку "Начать
                                # тестирование") т.к. это временный объект, в любом случае удаляется после полного
                                # завершения теста
                                quiz_set_instance.delete()

                            else:  # Если у пользователя остались попытки
                                # Удаляем результаты теста
                                results_instance.delete()

                                # Удаляем сгенерированный тест (был сформирован когда пользователь нажал кнопку "Начать
                                # тестирование") т.к. это временный объект, в любом случае удаляется после полного
                                # завершения теста
                                quiz_set_instance.delete()

                        context = {'user_name': user_name, 'ac_type': ac_type, 'timestamp': timestamp,
                                   'total_num_q': total_num_q, 'quize_name': quize_name,
                                   'correct_q_num': correct_q_num, 'total_result': total_result,
                                   'conclusion': conclusion, 'answers': answer_results,
                                   'min_pass_score': min_pass_score, 'total_mark': total_mark}

                        return render(request, 'results.html', context=context)

        else:
            return HttpResponseRedirect('/')
    except Exception as general_error:
        # Формируем письмо администратору
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        contence_of_mess = f'<b>File</b>:\n' \
                           f'{filename}\n' \
                           f'<b>Номер строки:</b> {line_number}\n\n' \
                           f'Вероятно пользователь обновил страницу с результатами теста'
        to = common.admin_email
        subject = f'!Серверная ошибка! Pilot Test'
        message = f'<p style="font-size: 20px;">Пользователь:</p>' \
                  f'<span style="font-size: 18px;"><b>{request.user.profile.position} </b></span>' \
                  f'<span style="font-size: 18px;"><b>{request.user.profile.ac_type}</b></span>' \
                  f'<p style="font-size: 18px;"><b>{request.user.profile.family_name} {request.user.profile.first_name}' \
                  f' {request.user.profile.middle_name}</b></p><br>' \
                  f'<p style="font-size: 20px;"><b>Текст ошибки:</b></p>' \
                  f'<p style="font-size: 18px;">{general_error}</p>' \
                  f'<p style="font-size: 20px;"><b>Сообщение:</b></p>' \
                  f'<p style="font-size: 18px;">{contence_of_mess}</p><br>' \
                  f'<a href="mailto:{request.user.email}">Ответить</a>'
        email_msg = {'subject': subject, 'message': message, 'to': to}
        common.send_email(request, email_msg)
        # Отправляем пользователя на заглавную страницу
        return HttpResponseRedirect('/')


@login_required
# @group_required('KRS')
# Все результаты тестов
def tests_results_list(request):
    groups = Group.objects.all().values()
    results_list_options = ['ТЕСТ СДАН', 'ТЕСТ НЕ СДАН', 'Все']
    group_list = []
    for group in groups:
        group_list.append(group)
    group_list.append({'name': 'Все'})  # Добавляем выбор всех групп
    position_list = Position.values
    position_list.append('Все')  # Добавляем вариант выбора всехдолжностей
    user_search_input = request.GET.get("user_search")
    filter_input = request.GET.getlist("filter")
    no_search_result = False
    if user_search_input or filter_input:
        if user_search_input:
            total_results_list = QuizeResults.objects.filter(Q(user_name__icontains=f'{user_search_input}'),
                                                             in_progress=False).order_by('-date_end')
            if not total_results_list:
                no_search_result = True
                results = f'Пилоты по запросу "{user_search_input}" не найдены'
                context = {'no_search_results': no_search_result, 'results': results, 'filter_input': filter_input,
                           'position_list': position_list, 'group_list': group_list,
                           'results_list_options': results_list_options, 'user_search_input': user_search_input}
                return render(request, 'tests_results_list.html', context=context)
            else:
                paginator = Paginator(total_results_list, 10)
                page_number = request.GET.get('page', 1)
                results_list_pages = paginator.page(page_number)
                context = {'results': results_list_pages, 'no_search_results': no_search_result,
                           'filter_input': filter_input,
                           'position_list': position_list, 'group_list': group_list,
                           'results_list_options': results_list_options, 'user_search_input': user_search_input}
                return render(request, 'tests_results_list.html', context=context)
        else:
            position = ''
            group = ''
            result = ''
            if filter_input[0] != 'Все':
                position = filter_input[0]
            if filter_input[1] != 'Все':
                group = filter_input[1]
            if filter_input[2] != 'Все':
                if filter_input[2] == 'ТЕСТ СДАН':
                    result = True
                else:
                    result = False
                total_user_list = QuizeResults.objects.filter(user_id__profile__position__icontains=position,
                                                              user_id__groups__name__icontains=group,
                                                              conclusion__exact=result,
                                                              in_progress=False).distinct().order_by('-date_end')
            else:
                total_user_list = QuizeResults.objects.filter(user_id__profile__position__icontains=position,
                                                              user_id__groups__name__icontains=group,
                                                              conclusion__icontains=result,
                                                              in_progress=False).distinct().order_by('-date_end')
            if not total_user_list:
                no_search_result = True
                results = f'Результаты тестов не найдены'
                context = {'no_search_results': no_search_result, 'results': results, 'filter_input': filter_input,
                           'position_list': position_list, 'group_list': group_list,
                           'results_list_options': results_list_options}
                return render(request, 'tests_results_list.html', context=context)
            else:
                #  Постраничная разбивка
                paginator = Paginator(total_user_list, 10)
                page_number = request.GET.get('page', 1)
                users = paginator.page(page_number)
                context = {'results': users, 'no_search_results': no_search_result, 'filter_input': filter_input,
                           'position_list': position_list, 'group_list': group_list,
                           'results_list_options': results_list_options}
                return render(request, 'tests_results_list.html', context=context)


    else:
        # Групы для полного списка тестов:
        groups = ['KRS', 'ПИ Штатные 737']
        if request.user.groups.filter(name__in=groups).exists() | request.user.is_superuser:
            results_list = QuizeResults.objects.filter(in_progress=False).order_by('-date_end')
        else:
            results_list = QuizeResults.objects.filter(in_progress=False,
                                                       user_id__username=request.user.username).order_by('-date_end')
        paginator = Paginator(results_list, 10)
        page_number = request.GET.get('page', 1)
        results_list_pages = paginator.page(page_number)
        context = {'results': results_list_pages, 'position_list': position_list, 'group_list': group_list,
                   'results_list_options': results_list_options}
        return render(request, 'tests_results_list.html', context=context)


@login_required
# @group_required('KRS')
# Детали результатов теста
def test_result_details(request, id):
    answer_results = []
    result = QuizeResults.objects.filter(id=id)
    answers = AnswersResults.objects.filter(user=result[0].user_id, results=result[0])
    for question in answers:
        question_block = {}
        question_block['question'] = question.question.question
        question_block['conclusion'] = question.conclusion
        #  Если вопрос имеет один ответ
        if not question.question.q_kind:
            options = []
            for i in range(1, 11):
                if question.question.answer == i:
                    options.append({f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                else:
                    if getattr(question.question, f'option_{i}'):
                        options.append({f'option': getattr(question.question, f'option_{i}'), 'valid': False})
            user_answer = question.user_answer
            question_block['answers'] = options
            question_block['user_answer'] = [getattr(question.question, f'option_{user_answer}')]

        #  Если на вопрос несколько ответов
        else:
            options = []
            #  Список с правильными ответами
            correct_answers_list = list(map(int, question.question.answers.split(',')))

            for i in range(1, 11):
                if i in correct_answers_list:
                    options.append({f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                else:
                    if getattr(question.question, f'option_{i}'):
                        options.append({f'option': getattr(question.question, f'option_{i}'), 'valid': False})

            question_block['answers'] = options
            user_answers = []
            for number in question.user_answer:
                if number.isdigit():
                    user_answers.append(number)
            answer = []
            for user_answer in user_answers:
                answer.append(getattr(question.question, f'option_{user_answer}'))
            question_block['user_answer'] = answer

        answer_results.append(question_block)

    #  Вынимаем и сохраняем адрес страницы, с которой пришёл пользователь
    previous_url = request.META.get('HTTP_REFERER')
    context = {'result': result, 'id': id, 'answers': answer_results, 'previous_url': previous_url}
    return render(request, 'test_result_details.html', context=context)


# Список вопросов из базы
@login_required
@group_required(('KRS', 'Редактор'))
def question_list(request):
    them_list = Thems.objects.all()
    user_search_input = request.GET.get("question_search")
    filter_input = request.GET.getlist("filter")
    ac_type_list = ACTypeQ.values  # Создаём список всех типов самолёта
    ac_type_list.append('Все')  # Добавляем вариант "Все"
    active_q_filter = ['Все', 'Активные', 'НЕ Активные']
    misc_filter = ['Все', 'АУЦ NWS', 'Кроме АУЦ NWS', 'На время', 'Не на время']
    # Если пользователь деактивировал вопрос
    if 'q_id' in request.GET:
        q_id = request.GET.get('q_id')
        q_object = QuestionSet.objects.get(id=q_id)
        if q_object.is_active:
            q_object.is_active = False
        else:
            q_object.is_active = True
        q_object.save()
        previous_url = request.META.get('HTTP_REFERER')
        return redirect(previous_url)
        # question_list = QuestionSet.objects.all()
        # q_count = question_list.count()
        # paginator = Paginator(question_list, 15)
        # page_number = request.GET.get('page', 1)
        # questions = paginator.page(page_number)
        # filtered = None
        # context = {'questions': questions, 'them_list': them_list, 'filtered': filtered, 'q_count': q_count,
        #            'ac_type': ac_type_list}
        # return render(request, 'question_list.html', context=context)

    no_search_result = False
    if user_search_input or filter_input:
        if user_search_input:
            total_questions_list = QuestionSet.objects.filter(Q(question__icontains=user_search_input))
            q_count = total_questions_list.count()
            if not total_questions_list:
                no_search_result = True
                results = f'Вопросы по запросу "{user_search_input}" не найдены'
                context = {'no_search_results': no_search_result, 'results': results, 'them_list': them_list,
                           'q_count': q_count, 'user_search_input': user_search_input,
                           'active_q_filter': active_q_filter, 'misc_filter': misc_filter}
                return render(request, 'question_list.html', context=context)
            else:
                paginator = Paginator(total_questions_list, 15)
                page_number = request.GET.get('page', 1)
                results_list_pages = paginator.page(page_number)
                context = {'questions': results_list_pages, 'no_search_results': no_search_result,
                           'them_list': them_list, 'q_count': q_count,
                           'user_search_input': user_search_input,
                           'active_q_filter': active_q_filter, 'misc_filter': misc_filter}
                return render(request, 'question_list.html', context=context)
        else:
            them = ''
            ac_type = ''
            if filter_input[0] != 'Все темы':
                them = filter_input[0]
            if filter_input[1] != 'Все':
                ac_type = filter_input[1]

            them_q_list = QuestionSet.objects.filter(them_name__name__icontains=them, ac_type__icontains=ac_type)
            if filter_input[2] != 'Все':  # Фильтруем Активные/Не активные вопросы
                if filter_input[2] == 'Активные':
                    them_q_list = them_q_list.filter(is_active=True)
                else:
                    them_q_list = them_q_list.filter(is_active=False)

            if filter_input[3] != 'Все':  # Фильтруем вопросы АУЦ
                if filter_input[3] == 'АУЦ NWS':
                    them_q_list = them_q_list.filter(is_for_center=True)
                elif filter_input[3] == 'Кроме АУЦ NWS':
                    them_q_list = them_q_list.filter(is_for_center=False)
                elif filter_input[3] == 'На время':
                    them_q_list = them_q_list.filter(is_timelimited=True)
                elif filter_input[3] == 'Не на время':
                    them_q_list = them_q_list.filter(is_timelimited=False)

            q_count = them_q_list.count()  # Подстчитываем количество вопросов
            paginator = Paginator(them_q_list, 15)
            page_number = request.GET.get('page', 1)
            results_list_pages = paginator.page(page_number)
            context = {'questions': results_list_pages, 'no_search_results': no_search_result,
                       'them_list': them_list, 'filter_input': filter_input, 'q_count': q_count,
                       'ac_type': ac_type_list, 'active_q_filter': active_q_filter,
                       'misc_filter': misc_filter}
            return render(request, 'question_list.html', context=context)
    else:
        question_list = QuestionSet.objects.all()
        q_count = question_list.count()
        paginator = Paginator(question_list, 15)
        page_number = request.GET.get('page', 1)
        questions = paginator.page(page_number)
        filtered = None
        context = {'questions': questions, 'them_list': them_list,
                   'filtered': filtered, 'q_count': q_count,
                   'ac_type': ac_type_list, 'active_q_filter': active_q_filter,
                   'misc_filter': misc_filter}
        return render(request, 'question_list.html', context=context)


# Добавить новый вопрос в базу вопросов
@login_required
@group_required(('KRS', 'Редактор'))
def new_question(request):
    #  Если пользователь нажал 'сохранить', выполняем проверку и сохраняем форму
    comments = {}  # Статические комментарии
    comments['Q_WEIGHT_COMMENT'] = text.Q_WEIGHT_COMMENT
    comments['MAX_PICTURE_FILE_SIZE'] = text.MAX_PICTURE_FILE_SIZE
    if request.method == 'POST':
        question_form = NewQuestionSetForm(request.POST, request.FILES)  # Для форм основанных на модели объекта
        if question_form.is_valid():
            dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            logger_user_action.warning(f'<b>Добавлен вопрос: </b>{request.POST.get("question")}\n\n'
                                       f'<b>User:</b> {request.user.profile.family_name}'
                                       f' {request.user.profile.first_name[0]}.'
                                       f'{request.user.profile.middle_name[0]}.')
            instance = question_form.save()
            instance.question_img = question_form.cleaned_data['question_img']
            instance.comment_img = question_form.cleaned_data['comment_img']
            instance.save()
            # print('path: ', f"{dir_path}/media/images/{instance.them_name.id}/{instance.id}/None/*.*")
            filelist = glob.glob(f"{dir_path}/media/images/{instance.them_name.id}/None/*.*")

            if filelist:
                for file in filelist:
                    os.remove(file)
            try:
                os.rmdir(f"{dir_path}/media/images/{instance.them_name.id}/None")
            except Exception:
                pass
            # Очищаем папку с временными файлами

            filelist = glob.glob(f"{dir_path}/media/images/tmp/*.*")
            if filelist:
                for file in filelist:
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            return redirect('quize737:question_list')
        else:
            context = {'question_form': question_form, 'q_id': 000, 'comments': comments}
            return render(request, 'new_question.html', context=context)

    else:
        question_form = NewQuestionSetForm()
        context = {'question_form': question_form, 'q_id': 000, 'comments': comments}
        return render(request, 'new_question.html', context=context)


# Редактирование конкретно взятого вопроса
@login_required
@group_required(('KRS', 'Редактор'))
def question_list_details(request, id):
    comments = {}  # Статические комментарии
    comments['Q_WEIGHT_COMMENT'] = text.Q_WEIGHT_COMMENT
    comments['MAX_PICTURE_FILE_SIZE'] = text.MAX_PICTURE_FILE_SIZE
    #  Если пользователь нажал 'сохранить', выполняем проверку и сохраняем форму
    if request.method == 'POST':
        #   Выясняем id вопроса для его обновления
        a = QuestionSet.objects.get(id=id)
        question_form = QuestionSetForm(request.POST, instance=a)  # Для форм основанных на модели объекта
        if question_form.is_valid():
            question_form.save()
            #  Возвращаем пользователя в исходный url
            previous_url = request.POST.get('previous_url', '/')

            return HttpResponseRedirect(previous_url)

        else:

            context = {'question_form': question_form, 'q_id': id, 'q_object': a, 'comments': comments}
            return render(request, 'question_list_details.html', context=context)

    elif 'q_switch_id' in request.GET:
        q_object = QuestionSet.objects.get(id=id)
        if q_object.is_active:
            q_object.is_active = False
        else:
            q_object.is_active = True
        q_object.save()
        q_object = QuestionSet.objects.get(id=id)
        question_form = QuestionSetForm(request.GET)
        # Сохраняем ссылку, с которой пришёл пользователь
        previous_url = request.GET.get('previous_url')
        context = {'question_form': question_form, 'q_id': id,
                   'previous_url': previous_url, 'q_object': q_object, 'comments': comments}
        return render(request, 'question_list_details.html', context=context)


    else:
        q_object = QuestionSet.objects.get(id=id)
        result = QuestionSet.objects.filter(id=id).values('them_name', 'question', 'option_1', 'option_2', 'option_3',
                                                          'option_4', 'option_5', 'option_6', 'option_7', 'option_8',
                                                          'option_9', 'option_10', 'q_kind', 'q_weight', 'answer',
                                                          'answers', 'id', 'ac_type', 'is_active', 'is_for_center',
                                                          'is_timelimited', 'comment_text')
        question_form = QuestionSetForm(result[0])
        # Сохраняем ссылку, с которой пришёл пользователь
        previous_url = request.META.get('HTTP_REFERER')
        context = {'question_form': question_form, 'q_id': result[0]['id'],
                   'previous_url': previous_url, 'q_object': q_object, 'comments': comments}
        return render(request, 'question_list_details.html', context=context)


# Удаляем вопрос
@login_required
@group_required(('KRS', 'Редактор'))
def question_del(request, id):
    question_instance = QuestionSet.objects.get(id=id)
    logger_user_action.warning(f'<b>Удалён вопрос: </b>{question_instance.question}\n\n'
                               f'<b>User:</b> {request.user.profile.family_name}'
                               f' {request.user.profile.first_name[0]}.'
                               f'{request.user.profile.middle_name[0]}.')
    QuestionSet.objects.get(id=id).delete()
    # print('URL_:', request.POST.get('previous_url'))
    previous_url = request.POST.get('previous_url')
    return HttpResponseRedirect(previous_url)
    # return redirect('quize737:question_list')


# Редактор тем вопросов
@login_required
@group_required(('KRS', 'Редактор'))
def theme_editor(request, id=None):
    if request.method == 'POST':
        form = NewThemeForm(request.POST)
        if form.is_valid():
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
            # ac_types_list = Profile.ACType.values  # Список типов ВС для фильтра
            # ac_types_list.append('Все')
            user_search_input = request.GET.get("them_search")
            theme_list = Thems.objects.exclude(name='Все темы')
            # theme_list = Thems.objects.all()
            them_num = Thems.objects.all().count() - 1
            q_num_dict = {}
            no_search_result = False
            if user_search_input:
                them_search_list = Thems.objects.filter(name__icontains=user_search_input)
                if not them_search_list:
                    no_search_result = True
                    results = f'Темы по запросу "{user_search_input}" не найдены'
                    context = {'no_search_results': no_search_result, 'results': results, 'them_num': 0}
                    return render(request, 'theme_editor.html', context=context)
                else:
                    for them in them_search_list:
                        q_num = QuestionSet.objects.filter(them_name=them).count()
                        q_num_dict[them.name] = q_num
                    them_num = them_search_list.count()
                    paginator = Paginator(them_search_list, 20)
                    page_number = request.GET.get('page', 1)
                    themes = paginator.page(page_number)
                    context = {'themes': themes, 'num_dict': q_num_dict, 'them_num': them_num}
                    return render(request, 'theme_editor.html', context=context)
            else:
                for them in theme_list:
                    q_num = QuestionSet.objects.filter(them_name=them).count()
                    q_num_dict[them.name] = q_num
                paginator = Paginator(theme_list, 20)
                page_number = request.GET.get('page', 1)
                themes = paginator.page(page_number)
                context = {'themes': themes, 'num_dict': q_num_dict, 'them_num': them_num}
                return render(request, 'theme_editor.html', context=context)


@login_required
@group_required(('KRS', 'Редактор Вопросов'))
#  Создание новой темы
def new_theme(request):
    form = NewThemeForm()
    if request.method == 'POST':
        form = NewThemeForm(request.POST)
        logger_user_action.warning(f'<b>Создана тема: </b>{request.POST.get("name")}\n\n'
                                   f'<b>User:</b> {request.user.profile.family_name}'
                                   f' {request.user.profile.first_name[0]}.'
                                   f'{request.user.profile.middle_name[0]}.')
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
@group_required(('KRS', 'Редактор'))
def theme_del(request, id):
    them_instance = Thems.objects.get(id=id)
    logger_user_action.warning(f'<b>Удалена Тема:</b> {them_instance.name}\n\n'
                               f'<b>User:</b> {request.user.profile.family_name}'
                               f' {request.user.profile.first_name[0]}.'
                               f'{request.user.profile.middle_name[0]}.')
    Thems.objects.get(id=id).delete()
    return redirect('quize737:theme_editor')


# Скачивание результата теста
@login_required
@group_required('KRS')
def download_test_result(request, id):
    result = QuizeResults.objects.filter(id=id).values()
    user_instance = User.objects.get(id=result[0]['user_id_id'])
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    # Выясняем тукущую директорию

    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    pdfmetrics.registerFont(TTFont('FreeSans', dir_path + '/static/FreeSans.ttf'))
    pdfmetrics.registerFont(TTFont('FreeSansBold', dir_path + '/static/FreeSansBold.ttf'))

    # p.setFillColorRGB(128, 128, 128) # Цвет текста
    # p. setStrokeColorRGB(0.2, 0.5, 0.3)
    # p.setFillColorRGB(128, 128, 128)  # choose fill colour
    # p.rect(1*inch, 1*inch, 200*inch, 200*inch, fill=1)  # draw rectangle

    y = 750

    # p.line(10, 700, 400, 700 * inch)

    p.drawInlineImage(dir_path + '/static/nws_logo_white.jpg', 0, y, width=260, height=100)
    x = 25  # Расстояние (отступ) текста справа (по горизонтали)
    y -= 25  # Расстояние (отступ) текста сверху (по вертикали)
    x_second = 190  # Расстояние (отступ справа) второй надписи в строке (динамическая информация)
    p.setFont('FreeSans', 23)
    p.drawString(120, y, f'Тестирование Лётного Состава')
    y -= 50
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Дата:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{result[0]["date_end"].strftime("%d.%m.%Y %H:%M:%S")} UTC')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'ФИО:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{result[0]["user_name"]}')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Квалификация:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{user_instance.profile.get_position_display()}')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Тип ВС:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{user_instance.profile.get_ac_type_display()}')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Название теста:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'"{result[0]["quize_name"]}"')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Количество вопросов:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{result[0]["total_num_q"]}')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Правильных ответов:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{result[0]["correct_q_num"]}')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Необходимо баллов:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{result[0]["pass_score"]}%')
    y -= 25
    p.setFont('FreeSans', 15)
    p.drawString(x, y, f'Набрано баллов:')
    p.setFont('FreeSansBold', 15)
    p.drawString(x_second, y, f'{result[0]["total_result"]}%')

    if result[0]["conclusion"] == True:
        total_result = 'ТЕСТ СДАН'
    else:
        total_result = 'ТЕСТ НЕ СДАН'
    y -= 70
    p.setFont('FreeSansBold', size=25)
    p.drawString(220, y, f'{total_result}')

    klo_sign = 'Командир Лётного Отряда ____________________ /                                /'

    if user_instance.profile.ac_type == 'B777' or 'B737':
        klo_sign = 'Командир ЛО B737/B777 ____________________ /                                /'
    elif user_instance.profile.ac_type == 'A32X' or 'A33X':
        klo_sign = 'Командир ЛО A321/A330 ____________________ /                                /'

    y -= 250
    p.setFont('FreeSans', size=13)
    p.drawString(x, y, f'{klo_sign}')

    p.showPage()
    p.save()
    buffer.seek(0)
    user_name = user_instance.profile.family_name + user_instance.profile.first_name[
                                                    :1] + user_instance.profile.middle_name[:1]

    result_for_file = ''
    result_id_for_file = str(result[0]['id'])
    if result[0]['conclusion']:
        result_for_file = "PASSED"
    else:
        result_for_file = "FAIL"

    filename = result_for_file + '_' + user_name + '_' + result_id_for_file  # Имя фала
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
    user_search_input = request.GET.get("test_search")
    no_search_result = False
    total_test_q_num = {}  # Общее количество вопросов в тесте
    total_test_theme = {}  # Темы в тесте
    total_user_test = {}  # Количество пользователей, которым назначен конкретный тест
    if user_search_input:
        total_test_list = TestConstructor.objects.filter(Q(name__icontains=f'{user_search_input}'))
        if not total_test_list:
            no_search_result = True
            results = f'Тесты по запросу "{user_search_input}" не найдены'
            context = {'no_search_results': no_search_result, 'results': results}
            return render(request, 'test_editor.html', context=context)
        else:
            for test in total_test_list:
                #  Вынимаем темы с количеством вопросов
                test_data = TestQuestionsBay.objects.filter(test_id=test)
                test_them_num = Thems.objects.all().count()
                users_number = UserTests.objects.filter(
                    test_name=test).count()  # Количество пользователей, которым назначен конкретный тест
                q_num = int()
                for q in test_data:

                    if q.theme.name == 'Все темы':
                        q_num = test_them_num * q.q_num
                    else:
                        q_num += q.q_num
                total_user_test[test.name] = users_number
                total_test_q_num[test.name] = q_num
                total_test_theme[test.name] = [x.theme.name for x in test_data]
            paginator = Paginator(total_test_list, 15)
            page_number = request.GET.get('page', 1)
            results_list_pages = paginator.page(page_number)
            context = {'tests_names': results_list_pages, 'no_search_results': no_search_result,
                       'total_q_num': total_test_q_num, 'total_them': total_test_theme, 'users': total_user_test}
            return render(request, 'test_editor.html', context=context)
    else:
        tests_names = TestConstructor.objects.all()
        #  Вынимаем общее количество вопросов по тесту
        for test in tests_names:
            #  Вынимаем темы с количеством вопросов
            test_data = TestQuestionsBay.objects.filter(test_id=test)
            test_them_num = Thems.objects.all().count() - 1
            users_number = UserTests.objects.filter(
                test_name=test).count()  # Количество пользователей, которым назначен конкретный тест
            q_num = int()
            for q in test_data:
                if q.theme.name == 'Все темы':
                    q_num = q_num + (int(test_them_num)) * q.q_num

                else:
                    q_num += q.q_num
            total_user_test[test.name] = users_number
            total_test_q_num[test.name] = q_num
            total_test_theme[test.name] = [x.theme.name for x in test_data]
        paginator = Paginator(tests_names, 15)
        page_number = request.GET.get('page', 1)
        tests_names_pages = paginator.page(page_number)
        context = {'tests_names': tests_names_pages, 'total_q_num': total_test_q_num, 'total_them': total_test_theme,
                   'users': total_user_test}
        return render(request, 'test_editor.html', context=context)


# Выбор Типа ВС в новом тесте
@login_required
@group_required('KRS')
def new_test_ac_type(request):
    ac_types_list = ACTypeP.values  # Список типов ВС для фильтра
    ac_types_list.append('Все')  # Добавляем в выбор вариант 'Все'
    context = {'ac_type': ac_types_list}
    return render(request, 'new_test_ac_type.html', context=context)


#  Продолжение создания нового теста после выбора типа ВС
@login_required
@group_required('KRS')
def create_new_test(request):
    krs_list = User.objects.filter(groups__name='KRS').order_by(
        'last_name')  # Вынимкаем список объектов группы KRS для выбора email адресов
    ac_type = request.GET.get('ac_type')
    thems = Thems.objects.all()
    total_q_num_per_them = {}
    # totla_q_num = 0
    target_them_num = 0  # Количество тем для подсчёта количества вопросов, если выбраны все темы
    min_q_them = []
    all_them_instance = Thems.objects.get(id=5)  # Instance объекта 'Все темы'
    for them_name in thems:
        # Считаем количество вопросов в каждой теме, кроме "Все темы"
        if them_name.id != 5:
            q_num = QuestionSet.objects.filter(Q(them_name=them_name), (Q(ac_type=ac_type) | Q(ac_type='ANY')),
                                               is_active=True).count()
            if q_num > 0:
                total_q_num_per_them[them_name] = q_num
                # totla_q_num += 1
                target_them_num += 1
                min_q_them.append(q_num)
    min_q_them.sort()
    total_q_num_per_them[all_them_instance] = min_q_them[0]  # Включаем 'Все темы' в список выбора тем
    thems_selection = []
    # Создаём список тем для конктретного типа ВС
    for them in total_q_num_per_them.keys():
        thems_selection.append((them.id, them.name))
    QuestionFormSet = formset_factory(MyNewTestFormQuestions, min_num=1, extra=0,
                                      formset=BaseArticleFormSet, can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        # if request.POST.get('test_name-comment'):
        comment = request.POST.get('test_name-comment')
        # if request.POST.get('test_name-for_user_comment'):
        for_user_comment = request.POST.get('test_name-for_user_comment')
        ac_type = request.POST.get('ac_type')  # Вынимаем Тип ВС
        test_q_set = QuestionFormSet(request.POST, request.FILES,
                                     form_kwargs={'thems_selection': tuple(thems_selection)},
                                     initial=[{'theme': '5', 'q_num': '4'}],
                                     prefix="questions")
        test_name_form = NewTestFormName(request.POST, prefix="test_name")
        #  Проверяем если установлен параметр тренировочного теста
        # if test_name_form.data['test_name-training'] == 'on':
        if 'test_name-training' in test_name_form.data.keys():
            if test_q_set.is_valid() and test_name_form.is_valid():
                # Создаём объект теста
                if 'test_name-set_mark' in test_name_form.data.keys():
                    mark_four = request.POST.get('test_name-mark_four')
                    mark_five = request.POST.get('test_name-mark_five')
                    new_test = TestConstructor.objects.create(name=test_name_form.data['test_name-name'],
                                                              pass_score=test_name_form.data['test_name-pass_score'],
                                                              training=True,
                                                              ac_type=ac_type,
                                                              set_mark=True,
                                                              mark_four=mark_four,
                                                              mark_five=mark_five,
                                                              comment=comment,
                                                              for_user_comment=for_user_comment
                                                              )
                else:
                    new_test = TestConstructor.objects.create(name=test_name_form.data['test_name-name'],
                                                              pass_score=test_name_form.data['test_name-pass_score'],
                                                              training=True,
                                                              ac_type=ac_type,
                                                              set_mark=False,
                                                              comment=comment,
                                                              for_user_comment=for_user_comment
                                                              )
                logger_user_action.warning(f'<b>Создан Тест: </b>{test_name_form.data["test_name-name"]}\n\n'
                                           f'<b>User:</b> {request.user.profile.family_name}'
                                           f' {request.user.profile.first_name[0]}.'
                                           f'{request.user.profile.middle_name[0]}.')

                # Создаём объекты вопросов теста
                for question in test_q_set.cleaned_data:
                    if not question['DELETE']:
                        them_instance = Thems.objects.get(id=question['theme'])
                        TestQuestionsBay.objects.create(theme=them_instance,
                                                        test_id=new_test,
                                                        q_num=question['q_num'])
                return redirect('quize737:test_editor')
            else:
                form_errors = []  # Ошибки при валидации формы
                for error in test_q_set.errors:
                    if len(error) > 0:
                        for value in error.values():
                            form_errors.append(value)
                errors_non_form = test_q_set.non_form_errors
                email_error = ''  # Ошибка с заполнением email адресов
                checked_emailes = ''  # Список email адресов для отсылки уведомлений
                # if 'krs_email' not in request.POST:
                #     email_error = 'Необходимо выбрать хотя бы один Email адрес для рассылки уведомлений'
                # else:
                #     checked_emailes = request.POST.getlist('krs_email')
                context = {'target_them_num': target_them_num, 'test_name_form': test_name_form,
                           'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                           'form_errors': form_errors, 'q_num_per_them': total_q_num_per_them, 'ac_type': ac_type,
                           'krs_list': krs_list, 'email_error': email_error, 'checked_emailes': checked_emailes}
                return render(request, 'new_test_form.html', context=context)
        else:  # Если тест НЕ тренировочный
            if test_q_set.is_valid() and test_name_form.is_valid() and 'krs_email' in request.POST:
                # Создаём объект теста
                emails = request.POST.getlist('krs_email')  # Вынимаем выбраные email адреса для рассылки
                if 'test_name-set_mark' in test_name_form.data.keys():
                    mark_four = request.POST.get('test_name-mark_four')
                    mark_five = request.POST.get('test_name-mark_five')
                    new_test = TestConstructor.objects.create(name=test_name_form.data['test_name-name'],
                                                              pass_score=test_name_form.data['test_name-pass_score'],
                                                              training=True,
                                                              ac_type=ac_type,
                                                              set_mark=True,
                                                              mark_four=mark_four,
                                                              mark_five=mark_five,
                                                              comment=comment,
                                                              for_user_comment=for_user_comment
                                                              )
                else:
                    new_test = TestConstructor.objects.create(name=test_name_form.data['test_name-name'],
                                                              pass_score=test_name_form.data['test_name-pass_score'],
                                                              training=False,
                                                              ac_type=ac_type,
                                                              email_to_send=', '.join(emails),
                                                              set_mark=False,
                                                              comment=comment,
                                                              for_user_comment=for_user_comment
                                                              )
                logger_user_action.warning(f'<b>Создан Тест: </b>{test_name_form.data["test_name-name"]}\n\n'
                                           f'<b>User:</b> {request.user.profile.family_name}'
                                           f' {request.user.profile.first_name[0]}.'
                                           f'{request.user.profile.middle_name[0]}.')
                # Создаём объекты вопросов теста
                for question in test_q_set.cleaned_data:
                    if not question['DELETE']:
                        them_instance = Thems.objects.get(id=question['theme'])
                        TestQuestionsBay.objects.create(theme=them_instance,
                                                        test_id=new_test,
                                                        q_num=question['q_num'])
                return redirect('quize737:test_editor')
            else:
                form_errors = []  # Ошибки при валидации формы
                for error in test_q_set.errors:
                    if len(error) > 0:
                        for value in error.values():
                            form_errors.append(value)
                errors_non_form = test_q_set.non_form_errors
                email_error = ''  # Ошибка с заполнением email адресов
                checked_emailes = ''  # Список email адресов для отсылки уведомлений
                if 'krs_email' not in request.POST:
                    email_error = 'Необходимо выбрать хотя бы один Email адрес для рассылки уведомлений'
                else:
                    checked_emailes = request.POST.getlist('krs_email')
                context = {'target_them_num': target_them_num, 'test_name_form': test_name_form,
                           'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                           'form_errors': form_errors, 'q_num_per_them': total_q_num_per_them, 'ac_type': ac_type,
                           'krs_list': krs_list, 'email_error': email_error, 'checked_emailes': checked_emailes}
                return render(request, 'new_test_form.html', context=context)
    else:
        # https://translated.turbopages.org/proxy_u/en-ru.ru.9354fe54-64555aae-631f0b43-74722d776562/https/docs.djangoproject.com/en/dev/topics/forms/formsets/#formsets
        test_name_form = NewTestFormName(prefix="test_name")
        test_q_set = QuestionFormSet(form_kwargs={'thems_selection': tuple(thems_selection)},
                                     initial=[{'theme': '5', 'q_num': '4', }], prefix='questions')

        context = {'target_them_num': target_them_num, 'test_name_form': test_name_form,
                   'test_q_set': test_q_set, 'q_num_per_them': total_q_num_per_them,
                   'ac_type': ac_type, 'krs_list': krs_list}
        return render(request, 'new_test_form.html', context=context)


@login_required
@group_required('KRS')
# Редактируем Детали уже существующего конекретного теста
def test_details(request, id):
    # Вынимаем список объектов группы KRS для выбора email адресов
    krs_list = User.objects.filter(groups__name='KRS').order_by(
        'last_name')
    # Вынимаем объект теста
    test_instance = TestConstructor.objects.filter(id=id).values('name', 'id', 'pass_score', 'training', 'ac_type',
                                                                 'email_to_send', 'set_mark', 'mark_four',
                                                                 'mark_five', 'comment', 'for_user_comment')
    ac_type = test_instance[0]['ac_type']

    #  Выбранные адреса email для рассылки
    checked_emailes = test_instance[0]['email_to_send']

    thems = Thems.objects.all()
    total_q_num_per_them = {}
    # totla_q_num = 0
    min_q_them = []
    target_them_num = 0  # Количество тем для подсчёта количества вопросов, если выбраны все темы
    all_them_instance = Thems.objects.get(id=5)  # Instance объекта 'Все темы'
    for them_name in thems:
        # Считаем количество вопросов в каждой теме, кроме "Все темы"
        if them_name.id != 5:
            q_num = QuestionSet.objects.filter(Q(them_name=them_name), (Q(ac_type=ac_type) | Q(ac_type='ANY')),
                                               is_active=True).count()
            if q_num > 0:
                total_q_num_per_them[them_name] = q_num
                # totla_q_num += 1
                min_q_them.append(q_num)
                target_them_num += 1
    min_q_them.sort()
    total_q_num_per_them[all_them_instance] = min_q_them[0]  # Включаем 'Все темы' в список выбора тем
    thems_selection = []
    # Создаём список тем для конктретного типа ВС
    for them in total_q_num_per_them.keys():
        thems_selection.append((them.id, them.name))
    #  Формируем форму
    QuestionFormSet = formset_factory(MyNewTestFormQuestions, min_num=1, extra=0,
                                      formset=BaseArticleFormSet, can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        a = TestConstructor.objects.get(id=id)
        test_name_form = NewTestFormName(request.POST)
        test_q_set = QuestionFormSet(request.POST, request.FILES,
                                     form_kwargs={'thems_selection': tuple(thems_selection)}, prefix="questions")

        a.name = test_name_form.data.get('name')
        a.pass_score = test_name_form.data.get('pass_score')
        a.comment = test_name_form.data.get('comment')
        a.for_user_comment = test_name_form.data.get('for_user_comment')
        if test_name_form.data.get('set_mark') == 'on':
            a.set_mark = True
            a.mark_four = test_name_form.data.get('mark_four')
            a.mark_five = test_name_form.data.get('mark_five')
        else:
            a.set_mark = False
        a.save()
        # Если выбран параметр тренировочного теста
        if test_name_form.data.get('training') == 'on':
            if test_q_set.is_valid():
                TestQuestionsBay.objects.filter(test_id=id).delete()
                a.training = True
                a.save()
                for question in test_q_set.cleaned_data:
                    if not question['DELETE']:
                        them_instance = Thems.objects.get(id=question['theme'])
                        TestQuestionsBay.objects.create(theme=them_instance,
                                                        test_id=a,
                                                        q_num=question['q_num'], )

                logger_user_action.warning(f'<b>Отредактирован Тест: </b>{a.name}\n\n'
                                           f'<b>User:</b> {request.user.profile.family_name}'
                                           f' {request.user.profile.first_name[0]}.'
                                           f'{request.user.profile.middle_name[0]}.')

                return redirect('quize737:test_editor')
            else:
                form_errors = []  # Ошибки при валидации формы
                for error in test_q_set.errors:
                    if len(error) > 0:
                        for value in error.values():
                            form_errors.append(value)
                errors_non_form = test_q_set.non_form_errors
                context = {'target_them_num': target_them_num, 'test_name_form': test_name_form,
                           'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                           'form_errors': form_errors, 'test_id': id, 'ac_type': test_instance[0]['ac_type'],
                           'krs_list': krs_list,
                           'q_num_per_them': total_q_num_per_them}
                return render(request, 'test_detailes.html', context=context)
        else:
            if test_q_set.is_valid() and 'krs_email' in request.POST:
                TestQuestionsBay.objects.filter(test_id=id).delete()
                emails = request.POST.getlist('krs_email')  # Вынимаем выбраные email адреса для рассылки
                a.email_to_send = ', '.join(emails)
                a.training = False
                a.save()
                for question in test_q_set.cleaned_data:
                    if not question['DELETE']:
                        them_instance = Thems.objects.get(id=question['theme'])
                        TestQuestionsBay.objects.create(theme=them_instance,
                                                        test_id=a,
                                                        q_num=question['q_num'], )

                logger_user_action.warning(f'<b>Отредактирован Тест: </b>{a.name}\n\n'
                                           f'<b>User:</b> {request.user.profile.family_name}'
                                           f' {request.user.profile.first_name[0]}.'
                                           f'{request.user.profile.middle_name[0]}.')

                return redirect('quize737:test_editor')
            else:
                form_errors = []  # Ошибки при валидации формы
                for error in test_q_set.errors:
                    if len(error) > 0:
                        for value in error.values():
                            form_errors.append(value)
                errors_non_form = test_q_set.non_form_errors
                email_error = ''  # Ошибка с заполнением email адресов
                checked_emailes = ''  # Список email адресов для отсылки уведомлений
                if 'krs_email' not in request.POST:
                    email_error = 'Необходимо выбрать хотя бы один Email адрес для рассылки уведомлений'
                else:
                    checked_emailes = request.POST.getlist('krs_email')
                context = {'target_them_num': target_them_num, 'test_name_form': test_name_form,
                           'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                           'form_errors': form_errors, 'test_id': id, 'ac_type': test_instance[0]['ac_type'],
                           'krs_list': krs_list, 'email_error': email_error, 'checked_emailes': checked_emailes,
                           'q_num_per_them': total_q_num_per_them}
                return render(request, 'test_detailes.html', context=context)
    else:
        previous_url = request.META.get('HTTP_REFERER')
        test_name_form = NewTestFormName(test_instance[0])  # Форма с названием теста
        test_questions = TestQuestionsBay.objects.filter(test_id=id).values('theme', 'q_num')
        # Создаём набор форм
        test_q_set = QuestionFormSet(form_kwargs={'thems_selection': tuple(thems_selection)}, initial=test_questions,
                                     prefix='questions')
        context = {'target_them_num': target_them_num, 'test_q_set': test_q_set, 'test_name_form': test_name_form,
                   'test_id': test_instance[0]['id'],
                   'q_num_per_them': total_q_num_per_them, 'ac_type': test_instance[0]['ac_type'], 'krs_list': krs_list,
                   'checked_emailes': checked_emailes, 'previous_url': previous_url}
        return render(request, 'test_detailes.html', context=context)


# Удаляем тест
@login_required
@group_required('KRS')
def del_test(request, id):
    a = TestConstructor.objects.get(id=id)
    logger_user_action.warning(f'<b>Удалён Тест: </b>{a.name}\n\n'
                               f'<b>User:</b> {request.user.profile.family_name}'
                               f' {request.user.profile.first_name[0]}.'
                               f'{request.user.profile.middle_name[0]}.')
    TestConstructor.objects.get(id=id).delete()
    return redirect('quize737:test_editor')


@login_required
@group_required('KRS')
def user_list(request):
    if request.method == 'POST':
        pass

    else:
        # Если в запросе были отмечены пользователи (user_select)
        selected_user_list = []  # Список пользователей, которые были отмечены
        # Пользователи у которых просрочена дата теста
        user_test_out_of_try = {}  # User_ID:Test_Name
        user_test_out_of_date = {}  # User_ID:Test_Name
        total_user_expire_tests = []

        # total_expired_user_tests = (UserTests.objects.filter((Q(num_try__lte=0) &
        #                                                       Q(user__quizeresults__in_progress=False) &
        #                                                       Q(results_id=F('user__quizeresults__id'))) |
        #                                                      Q(date_before__lt=datetime.date.today()))
        #                             .order_by('date_before').distinct())
        # Формируем словарь с просроченными по попыткам тестами
        for test in UserTests.objects.filter(Q(num_try__lte=0) &
                                             Q(user__quizeresults__in_progress=False) &
                                             Q(results_id=F('user__quizeresults__id'))).distinct():
            user_test_out_of_try[test.user.id] = test.test_name.name
        # Формируем словарь с просроченными по дате тестами
        for test in UserTests.objects.filter(date_before__lt=datetime.date.today()).distinct():
            user_test_out_of_date[test.user.id] = test.test_name.name
        # Добавляем инфу о просроченных тестав в один список
        total_user_expire_tests.append(user_test_out_of_try)
        total_user_expire_tests.append(user_test_out_of_date)

        # print('TOTAL:', total_user_expire_tests)

        if 'user_selected' in request.GET.keys():
            selected_users_ids = request.GET.getlist('user_selected')
            for user_id in set(selected_users_ids):  # Переводим список во множество, что бы элементы не повторялись
                user_selected = User.objects.get(id=user_id)
                selected_user_list.append(user_selected)

        groups = Group.objects.all().values()  # Список всех групп для фильтра
        tests = TestConstructor.objects.all().values()  # Список всех тестов для фильтра
        assign_test_list = UserTests.objects.all()  # Все тесты, назначенные кому либо
        user_test_dict = {}  # Словарь с тестами пользователей
        #  Формируем словаль 'Пользователь - назначенные тесты'
        for user_tests in assign_test_list:
            user_test_dict.setdefault(user_tests.user.username, []).append(user_tests.test_name.name)
        group_list = []
        test_list = []
        for group in groups:
            group_list.append(group)
        for test in tests:
            test_list.append(test)
        group_list.append({'name': 'Все'})  # Добавляем выбор всех групп
        test_list.append({'name': 'Все'})  # Добавляем выбор всех тестов
        test_list.append({'name': 'Просроченные'})
        position_list = Position.values
        position_list.append('Все')  # Добавляем вариант выбора всех должностей
        ac_types_list = ACTypeP.values  # Список типов ВС для фильтра
        ac_types_list.append('Все')
        user_search_input = request.GET.get("user_search")
        filter_input = request.GET.getlist("position_filter")

        no_search_result = False
        if user_search_input or filter_input:
            if user_search_input:
                user_search_data = request.GET.get("user_search").split()
                if len(user_search_data) == 3:
                    total_user_list = User.objects.filter(Q(profile__family_name__icontains=f'{user_search_data[0]}'),
                                                          Q(profile__first_name__icontains=f'{user_search_data[1]}'),
                                                          Q(profile__middle_name__icontains=f'{user_search_data[2]}'),
                                                          is_active=True).exclude(
                        username='roman')
                elif len(user_search_data) == 2:
                    total_user_list = User.objects.filter(Q(profile__family_name__icontains=f'{user_search_data[0]}'),
                                                          Q(profile__first_name__icontains=f'{user_search_data[1]}'),
                                                          is_active=True).exclude(
                        username='roman')
                    if not total_user_list:
                        total_user_list = User.objects.filter(
                            Q(profile__first_name__icontains=f'{user_search_data[0]}'),
                            Q(profile__middle_name__icontains=f'{user_search_data[1]}'),
                            is_active=True).exclude(username='roman')
                elif len(user_search_data) == 1:
                    total_user_list = User.objects.filter(
                        Q(profile__family_name__icontains=f'{user_search_data[0]}') | Q(
                            profile__first_name__icontains=f'{user_search_data[0]}') | Q(
                            profile__middle_name__icontains=f'{user_search_data[0]}'),
                        is_active=True).exclude(username='roman')
                else:
                    no_search_result = True
                    results = f'Пилоты по запросу "{user_search_input}" не найдены'
                    context = {'no_search_results': no_search_result, 'results': results,
                               'position_list': position_list, 'group_list': group_list, 'ac_types': ac_types_list,
                               'user_search_input': user_search_input, 'selected_users': selected_user_list,
                               'user_list': selected_user_list, 'expire_tests': total_user_expire_tests}
                    return render(request, 'user_list.html', context=context)
                if not total_user_list:
                    no_search_result = True
                    results = f'Пилоты по запросу "{user_search_input}" не найдены'
                    context = {'no_search_results': no_search_result, 'results': results,
                               'position_list': position_list, 'group_list': group_list,
                               'assign_test_list': assign_test_list, 'ac_types': ac_types_list, 'tests_list': test_list,
                               'user_search_input': user_search_input, 'selected_users': selected_user_list,
                               'user_list': selected_user_list, 'expire_tests': total_user_expire_tests}
                    return render(request, 'user_list.html', context=context)
                else:
                    total_user_number = len(total_user_list)
                    paginator = Paginator(total_user_list, 25)
                    page_number = request.GET.get('page', 1)
                    users = paginator.page(page_number)
                    context = {'user_list': users, 'no_search_results': no_search_result,
                               'position_list': position_list, 'group_list': group_list, 'tests_list': test_list,
                               'user_test_dict': user_test_dict, 'user_num': total_user_number,
                               'ac_types': ac_types_list, 'user_search_input': user_search_input,
                               'selected_users': selected_user_list, 'expire_tests': total_user_expire_tests}
                    return render(request, 'user_list.html', context=context)
            else:
                ac_type = ''
                position = ''
                group = ''
                test = ''
                if filter_input[0] != 'Все':
                    ac_type = filter_input[0]
                if filter_input[1] != 'Все':
                    position = filter_input[1]
                if filter_input[2] != 'Все':
                    group = filter_input[2]
                if filter_input[3] != 'Все':
                    if filter_input[3] == 'Просроченные':

                        total_user_list = User.objects.filter(profile__ac_type__contains=ac_type,
                                                              profile__position__contains=position,
                                                              groups__name__contains=group,
                                                              is_active=True,
                                                              ).exclude(
                            username='roman').distinct().order_by('last_name')
                        total_user_list = total_user_list.filter(
                            Q(usertests__num_try__lte=0) | Q(usertests__date_before__lt=datetime.date.today()))
                    else:
                        test = filter_input[3]
                        total_user_list = User.objects.filter(profile__ac_type__contains=ac_type,
                                                              profile__position__contains=position,
                                                              groups__name__contains=group,
                                                              usertests__test_name__name=test,
                                                              is_active=True).exclude(
                            username='roman').distinct().order_by('last_name')
                else:
                    total_user_list = User.objects.filter(profile__ac_type__icontains=ac_type,
                                                          profile__position__icontains=position,
                                                          groups__name__icontains=group,
                                                          is_active=True).exclude(
                        username='roman').distinct().order_by('last_name')
                if not total_user_list:
                    no_search_result = True
                    results = f'Пилоты по запросу не найдены'
                    context = {'no_search_results': no_search_result, 'results': results, 'filter_input': filter_input,
                               'position_list': position_list, 'group_list': group_list, 'tests_list': test_list,
                               'ac_types': ac_types_list, 'selected_users': selected_user_list,
                               'user_list': selected_user_list, 'expire_tests': total_user_expire_tests}
                    return render(request, 'user_list.html', context=context)
                else:
                    total_user_number = len(total_user_list)
                    paginator = Paginator(total_user_list, 20)
                    page_number = request.GET.get('page', 1)
                    users = paginator.page(page_number)
                    context = {'user_list': users, 'no_search_results': no_search_result,
                               'position_list': position_list, 'filter_input': filter_input,
                               'group_list': group_list, 'tests_list': test_list, 'user_test_dict': user_test_dict,
                               'user_num': total_user_number, 'ac_types': ac_types_list,
                               'selected_users': selected_user_list, 'expire_tests': total_user_expire_tests}
                    return render(request, 'user_list.html', context=context)

        else:

            total_user_list = User.objects.all().order_by('last_name').filter(is_active=True).exclude(
                username='roman')  # Вынимаем всех пользователей, кроме superuser
            total_user_number = User.objects.all().filter(is_active=True).exclude(username='roman').count()
            #  Постраничная разбивка
            paginator = Paginator(total_user_list, 20)
            page_number = request.GET.get('page', 1)
            users = paginator.page(page_number)

            context = {'user_list': users, 'no_search_results': no_search_result, 'position_list': position_list,
                       'group_list': group_list, 'tests_list': test_list, 'user_test_dict': user_test_dict,
                       'user_num': total_user_number, 'ac_types': ac_types_list, 'selected_users': selected_user_list,
                       'expire_tests': total_user_expire_tests}
            return render(request, 'user_list.html', context=context)


# Список пользователей конкретной группы
@login_required
@group_required('KRS')
def group_users(request, id):
    tests = TestConstructor.objects.all().values()  # Список всех тестов для фильтра
    test_list = []
    for test in tests:
        test_list.append(test)
    test_list.append({'name': 'Все'})  # Добавляем выбор всех тестов
    position_list = Position.values
    position_list.append('Все')  # Добавляем вариант выбора всех должностей
    ac_types_list = ACTypeP.values  # Список типов ВС для фильтра
    ac_types_list.append('Все')
    groups = Group.objects.all().values()
    group_list = []
    for group in groups:
        group_list.append(group)
    group_list.append({'name': 'Все'})  # Добавляем выбор всех групп
    position_list = Position.values
    position_list.append('Все')  # Добавляем вариант выбора всехдолжностей
    no_search_result = False
    total_user_list = User.objects.filter(groups=id).order_by('last_name')
    total_user_number = User.objects.filter(groups=id).count()  # Получаем число пользователей группы
    group_instance = Group.objects.get(id=id)
    filter_input = ['Все', 'Все', group_instance.name, 'Все']

    if not total_user_list:
        no_search_result = True
        group_name = Group.objects.get(id=id)  # .values('name')
        results = f'Пилоты в группе "{group_name.name}" не найдены'
        context = {'no_search_results': no_search_result, 'results': results,
                   'position_list': position_list, 'group_list': group_list, 'ac_types': ac_types_list}
        return render(request, 'user_list.html', context=context)
    paginator = Paginator(total_user_list, 20)
    page_number = request.GET.get('page', 1)
    users = paginator.page(page_number)
    context = {'user_list': users, 'no_search_results': no_search_result, 'position_list': position_list,
               'user_num': total_user_number,
               'group_list': group_list, 'ac_types': ac_types_list, 'tests_list': test_list,
               'filter_input': filter_input}
    return render(request, 'user_list.html', context=context)


@login_required
@group_required('KRS')
def group_list(request, id=None):
    if request.method == 'POST':
        pass
    if id:
        pass
    else:
        group_user_num = {}  # Количество пользователей в группе
        groups = Group.objects.all()
        for group in groups:
            user_num = User.objects.filter(groups=group.id).count()
            group_user_num[group.name] = user_num
        fixed_groups = common.fixed_groups
        paginator = Paginator(groups, 20)
        page_number = request.GET.get('page', 1)
        groups_pages = paginator.page(page_number)
        context = {'groups': groups_pages, 'fixed_groups': fixed_groups, 'group_user_num': group_user_num}
        return render(request, 'group_list.html', context=context)


# Обрабатываем вызов деталей конкретной группы для назначения тестов
@login_required
@group_required('KRS')
def group_details(request, id):
    UserTestForm = formset_factory(TestsForUser, extra=0, formset=BaseUserTestFormSet,
                                   can_delete=True)  # Extra - количество строк формы
    group = Group.objects.get(id=id)
    if request.method == 'POST':
        tests_for_group_form = UserTestForm(request.POST,
                                            request.FILES)  # Вынимаем данные из запроса и заполняем ими форму
        if tests_for_group_form.is_valid():
            for test in tests_for_group_form.cleaned_data:
                #  Удаляем все объекты
                # Проверяем было ли указано имя объекта
                try:
                    if UserTests.objects.get(test_name=test['test_name']):
                        UserTests.objects.filter(test_name=test['test_name']).delete()
                except Exception:
                    pass
                # Создаём только те объекты, которые не помечены для удаления
                if not test['DELETE']:
                    #  Вынимаем всех пользователей группы
                    total_user_list = User.objects.filter(groups=id)

                    #  Перебираем всех пользователей группы
                    for user in total_user_list:
                        # Проверяем есть ли у пользователя этот тест
                        try:
                            user_test_exists = UserTests.objects.get(user=user, test_name=test['test_name'])
                        except UserTests.DoesNotExist:
                            user_test_exists = None
                        if user_test_exists is None:
                            UserTests.objects.create(user=user,
                                                     test_name=test['test_name'],
                                                     num_try_initial=test['num_try'],
                                                     num_try=test['num_try'],
                                                     date_before=test['date_before'])

                            #  Отправляем письмо пользователю о назначенном тесте
                            subject = f"Вам назначен Тест: '{test['test_name']}'"
                            message = f"<p style='font-size: 25px;'><b>Уважаемый, {user.profile.first_name} {user.profile.middle_name}.</b></p><br>" \
                                      f"<p style='font-size: 20px;'>Вам назначен тест: <b>'{test['test_name']}'</b></p>" \
                                      f"<p style='font-size: 20px;'>На портале {config('SITE_URL', default='')}</p>" \
                                      f"<p style='font-size: 20px;'>Тест необходимо выполнить до <b>{test['date_before'].strftime('%d.%m.%Y')}</b></p>"

                            email_msg = {'subject': subject, 'message': message, 'to': user.email}
                            send_email(request, email_msg)

            # Загружаем новые данные в форму
            # user_tests = UserTests.objects.filter(user=id).values('test_name', 'num_try', 'date_before')
            # tests_for_user_form = UserTestForm(initial=user_tests)
            context = {'group': group, 'test_and_data_saved': True}
            return render(request, 'group_details.html', context=context)

        else:
            form_errors = []  # Ошибки при валидации формы
            for error in tests_for_group_form.errors:
                if len(error) > 0:
                    for value in error.values():
                        form_errors.append(value)
            errors_non_form = tests_for_group_form.non_form_errors
            context = {'group': group, 'group_tests': tests_for_group_form,
                       'non_form_errors': errors_non_form,
                       'form_errors': form_errors, 'group_id': id}
            return render(request, 'group_details.html', context=context)
    else:
        tests_for_group_form = UserTestForm()

        context = {'group': group, 'group_tests': tests_for_group_form, 'group_id': id}
        return render(request, 'group_details.html', context=context)


#  Создание новой группы
@login_required
@group_required('KRS')
def new_group(request):
    if request.method == 'POST':
        group_form = GroupForm(request.POST)
        if group_form.is_valid():
            group = Group.objects.create(name=group_form.cleaned_data.get('group_name'))  # Добавить группу разрешений
            # group.save()
            GroupsDescription.objects.create(group=group,
                                             discription=group_form.cleaned_data.get('discription')
                                             )
            logger_user_action.warning(f'<b>Создана Группа: </b>{group.name}\n\n'
                                       f'<b>User:</b> {request.user.profile.family_name}'
                                       f' {request.user.profile.first_name[0]}.'
                                       f'{request.user.profile.middle_name[0]}.')
            return redirect('quize737:group_list')
        else:
            context = {'form': group_form}
            return render(request, 'new_group.html', context=context)
    else:
        group_form = GroupForm()
        context = {'form': group_form}
        return render(request, 'new_group.html', context=context)


@login_required
@group_required('KRS')
def edit_group(request, id):
    group_obj = Group.objects.get(id=id)

    if request.method == 'POST':
        group_form = EditGroupForm(request.POST, instance=group_obj)
        discript_obj = GroupsDescription.objects.get(group=group_obj)
        if group_form.is_valid():
            group_obj.name = group_form.cleaned_data['group_name']
            group_obj.save()
            discript_obj.discription = group_form.cleaned_data['discription']
            discript_obj.save()

            logger_user_action.warning(f'<b>Отредактирована Группа: </b>{group_obj.name}\n\n'
                                       f'<b>User:</b> {request.user.profile.family_name}'
                                       f' {request.user.profile.first_name[0]}.'
                                       f'{request.user.profile.middle_name[0]}.')

            return redirect('quize737:group_list')
        else:
            context = {'group_form': group_form}
            return render(request, 'edit_group.html', context=context)
    else:
        group_form = EditGroupForm(
            initial={"group_name": group_obj.name, 'discription': group_obj.groupsdescription.discription})
        context = {'group_form': group_form}
        return render(request, 'edit_group.html', context=context)


#  Удаление группы
@login_required
@group_required('KRS')
def group_del(request, id):
    group_obj = Group.objects.get(id=id)
    logger_user_action.warning(f'<b>Удалена Группа: </b>{group_obj.name}\n\n'
                               f'<b>User:</b> {request.user.profile.family_name}'
                               f' {request.user.profile.first_name[0]}.'
                               f'{request.user.profile.middle_name[0]}.')

    Group.objects.get(id=id).delete()
    return redirect('quize737:group_list')


@login_required
@group_required('KRS')
def edit_user(request, id):
    position_list = Position.labels  # Вырианты выбора должности пилота
    ac_type_list = ACTypeP.labels  # Варианты выбора типа ВС пилота
    user_obj = User.objects.get(id=id)  # Объект пользователя
    all_groups = Group.objects.all()  # Все существующие группы
    if request.method == 'POST':
        form_user = EditUserForm(request.POST, instance=user_obj)
        form_profile = EditProfileForm(request.POST, instance=user_obj)
        new_position = request.POST.get('position')  # Новая должность
        changed_groups = request.POST.getlist('group')  # Новые группы
        new_ac_type = request.POST.get('ac_type')  # Новый тип ВС
        old_position = user_obj.profile.position  # Текущая (старая) должность
        old_ac_type = user_obj.profile.ac_type  # Текущий (старый) тип ВС

        logger_user_action.warning(f'<b>Изменены данные Пилота: </b>{user_obj.profile.family_name}'
                                   f'{user_obj.profile.first_name[0]}.'
                                   f'{user_obj.profile.middle_name[0]}.\n\n'
                                   f'<b>User:</b> {request.user.profile.family_name}'
                                   f' {request.user.profile.first_name[0]}.'
                                   f'{request.user.profile.middle_name[0]}.')

        UserChangeLog.objects.create(user_changed=user_obj,
                                     description="Изм. данных",
                                     user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                     )

        # Проверяем должность (квалификацию), при необходимости обновляем должность и группу
        for j in Position.choices:  # Выясняем соответсвие названию выбора и самому выбору
            if j[1] == new_position:
                new_position = j[0]
                break
        position_name_group = ''
        if old_position != new_position:
            user_obj.profile.position = new_position
            user_obj.profile.save()

            position_name_group = new_position + ' ' + user_obj.profile.ac_type

        all_groups_set = set()  # Множество для хранения стринговых названий групп
        for group in all_groups:  # Составляем множество из существующих групп
            all_groups_set.add(str(group.name))
        to_del_groups = list(set(all_groups_set) - set(changed_groups))  # Группы, в которых пользователь не участвует

        # Устанавливаем группу в соответствии с выбранной должностью, если она была изменена
        if position_name_group:  # Если поменяли должность, то переменная новой группы пользователя будет заполнена
            if position_name_group in to_del_groups:  # Убираем новую группу из удаляемых групп
                to_del_groups.remove(position_name_group)
            if position_name_group not in changed_groups:  # Добавляем новую группу в назначаемые группы
                changed_groups.append(position_name_group)
            #  Выясняем старую группу пользователя
            position_name_group_old = old_position + ' ' + user_obj.profile.ac_type
            if position_name_group_old not in to_del_groups:  # Добавляем старую группу в удаляемые, если ее там нет
                to_del_groups.append(position_name_group_old)
            if position_name_group_old in changed_groups:  # Удаляем старую группу из назначенных, если она там есть
                changed_groups.remove(position_name_group_old)

        for del_group in to_del_groups:  # Удаляем пользователя из групп
            group_obj = Group.objects.get(name=del_group)
            user_obj.groups.remove(group_obj)

        for add_group in changed_groups:  # Добавляем пользователя в группы
            group_obj = Group.objects.get(name=add_group)
            user_obj.groups.add(group_obj)

        #  Проверям ТИП ВС
        for j in ACTypeP.choices:  # Выясняем соответсвие названию выбора и самому выбору
            if j[1] == new_ac_type:
                new_ac_type = j[0]
                break
        if old_ac_type != new_ac_type:
            user_obj.profile.ac_type = new_ac_type
            user_obj.profile.save()

        # TODO: долелать автоматическое изменение группы, в случаем изменения типа ВС

        # Проверяем форму Логина и Email

        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            # form_profile.save()

            # user_obj.username = form_user.cleaned_data['username']
            # user_obj.email = form_user.cleaned_data['email']
            user_obj.first_name = form_profile.cleaned_data['first_name']
            user_obj.last_name = form_profile.cleaned_data['family_name']
            user_obj.save()
            user_obj.profile.family_name = form_profile.cleaned_data['family_name']
            user_obj.profile.first_name = form_profile.cleaned_data['first_name']
            user_obj.profile.middle_name = form_profile.cleaned_data['middle_name']
            user_obj.profile.save()

            # Возвращаем пользователя на исходную страницу
            previous_url = request.POST.get('previous_url', '/')

            # TODO: проверить работу на реальном сервере
            #  Вынимаем чистый хост на для тестового сервере
            request_host = request.get_host()
            index = (request.get_host()).find(':')
            request_host = request_host[:index]
            # if previous_url and urlparse(previous_url).hostname == request_host:
            return HttpResponseRedirect(previous_url)
            # else:
            #     return redirect('quize737:user_list')

        else:
            form_user = EditUserForm(request.POST, instance=user_obj)
            form_profile = EditProfileForm(request.POST, instance=user_obj)
            context = {'user_obj': user_obj, 'all_groups': all_groups, 'position_list': position_list,
                       'form_user': form_user, 'form_profile': form_profile, 'ac_type': ac_type_list}
            return render(request, 'edit_user.html', context=context)
    else:
        #  Вынимаем и сохраняем адрес страницы, с которой пришёл пользователь
        if 'previous_url' in request.GET.keys():
            previous_url = request.GET.get('previous_url')
        else:
            previous_url = request.META.get('HTTP_REFERER')
        form_user = EditUserForm(initial={"username": user_obj.username, 'email': user_obj.email})
        form_profile = EditProfileForm(initial={'family_name': user_obj.profile.family_name,
                                                'first_name': user_obj.profile.first_name,
                                                'middle_name': user_obj.profile.middle_name})
        context = {'user_obj': user_obj, 'all_groups': all_groups, 'position_list': position_list,
                   'form_user': form_user, 'form_profile': form_profile, 'ac_type': ac_type_list,
                   'previous_url': previous_url}
        return render(request, 'edit_user.html', context=context)


@login_required
@group_required('KRS')
# Обрабатываем вызов деталей конкретного пользователя для назначения тестов
def user_detales(request, id):
    UserTestForm = formset_factory(TestsForUser, extra=0, formset=BaseUserTestFormSet,
                                   can_delete=True)  # Extra - количество строк формы
    user_object = User.objects.get(id=id)
    user_profile = Profile.objects.filter(user=user_object)

    # sent = False  # Переменная для отправки письма

    if request.method == 'POST':
        previous_url = request.POST.get('previous_url')
        tests_for_user_form = UserTestForm(request.POST, request.FILES)
        if tests_for_user_form.is_valid():
            for test in tests_for_user_form.cleaned_data:

                #  Удаляем все объекты
                if test['DELETE']:
                    UserTests.objects.filter(user=user_object,
                                             test_name=test['test_name']).delete()  # Удаляем тест у пользователя
                    logger_user_action.warning(f'У Пользователя: '
                                               f'<b>{user_object.profile.family_name} '
                                               f'{user_object.profile.first_name[0]}.'
                                               f'{user_object.profile.middle_name[0]}.</b>\n'
                                               f'Удалён Тест: <b>{test["test_name"]}</b>\n\n'
                                               f'<b>User: </b>{request.user.profile.family_name}'
                                               f' {request.user.profile.first_name[0]}.'
                                               f'{request.user.profile.middle_name[0]}.')
                    UserChangeLog.objects.create(user_changed=user_object,
                                                 description="Удалён Тест",
                                                 test_id=test['test_name'].id,
                                                 test_name=test["test_name"],
                                                 user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                 )

                    try:  # Ищем и удаляем начатые, но не законченные тесты (сам сформированный временный тест с вопросами)
                        QuizeSet.objects.get(user_under_test=user_object.username,
                                             quize_name=test['test_name']).delete()
                    except Exception:
                        pass
                    try:  # Ищем и удаляем результаты теста, если есть не законченные (in_progress=True)
                        result_instance = QuizeResults.objects.get(user_id=user_object, quize_name=test['test_name'])
                        if result_instance.in_progress:
                            result_instance.delete()
                    except Exception:
                        pass
                else:
                    try:
                        if UserTests.objects.get(user=user_object, test_name=test['test_name']):
                            instance = UserTests.objects.get(user=user_object, test_name=test['test_name'])
                            # Если изменено количество попыток или срок сдачи теста информируем пользователя
                            if int(instance.num_try) != int(test['num_try']) or instance.date_before != test[
                                'date_before']:
                                def test_param_check() -> str:
                                    text = ''
                                    if int(instance.num_try) != int(test['num_try']) and instance.date_before != test[
                                        'date_before']:
                                        text = f'Кол-во попыток было: {instance.num_try}\n<br>' \
                                               f'Кол-во попыток установлено: {test["num_try"]}\n<br>' \
                                               f'Выполнить до было: {instance.date_before.strftime("%d.%m.%Y")}\n<br>' \
                                               f'Выполнить до установлено: {test["date_before"].strftime("%d.%m.%Y")}<br>'
                                        # Записываем журнал, для просмотра пользователем
                                        UserChangeLog.objects.create(user_changed=user_object,
                                                                     description="Кол-во попыток",
                                                                     test_id=test['test_name'].id,
                                                                     test_name=test["test_name"],
                                                                     old_num_try=instance.num_try,
                                                                     new_num_try=int(test["num_try"]),
                                                                     user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                                     )
                                        # Записываем журнал, для просмотра пользователем
                                        UserChangeLog.objects.create(user_changed=user_object,
                                                                     description="Изм. дата",
                                                                     test_id=test['test_name'].id,
                                                                     test_name=test["test_name"],
                                                                     old_date=instance.date_before,
                                                                     new_date=test["date_before"],
                                                                     user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                                     )

                                    elif int(instance.num_try) != int(test['num_try']) or instance.date_before != test[
                                        'date_before']:
                                        if int(instance.num_try) != int(test['num_try']):
                                            text = f'Кол-во попыток было: {instance.num_try}<br>\n' \
                                                   f'Кол-во попыток установлено: {test["num_try"]}<br>\n'
                                            # Записываем журнал, для просмотра пользователем
                                            UserChangeLog.objects.create(user_changed=user_object,
                                                                         description="Кол-во попыток",
                                                                         test_id=test['test_name'].id,
                                                                         test_name=test["test_name"],
                                                                         old_num_try=instance.num_try,
                                                                         new_num_try=int(test["num_try"]),
                                                                         user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                                         )
                                        else:
                                            text = f'Выполнить до было: {instance.date_before.strftime("%d.%m.%Y")}<br>\n' \
                                                   f'Выполнить до установлено: {test["date_before"].strftime("%d.%m.%Y")}<br>'
                                            UserChangeLog.objects.create(user_changed=user_object,
                                                                         description="Изм. дата",
                                                                         test_id=test['test_name'].id,
                                                                         test_name=test["test_name"],
                                                                         old_date=instance.date_before,
                                                                         new_date=test["date_before"],
                                                                         user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                                         )
                                    return text

                                # Формируем текст сообщения
                                info_text = test_param_check()
                                #  Записываем лог
                                logger_user_action.warning(f'Изменены параметры теста пользователя: '
                                                           f'<b>{user_object.profile.family_name} </b>'
                                                           f'{user_object.profile.first_name[0]}.'
                                                           f'{user_object.profile.middle_name[0]}.\n'
                                                           f'Тест: <b>{test["test_name"]}</b>\n'
                                                           f'{info_text}\n\n'
                                                           f'<b>User: </b>{request.user.profile.family_name}'
                                                           f' {request.user.profile.first_name[0]}.'
                                                           f'{request.user.profile.middle_name[0]}.')

                                #  Отправляем письмо пользователю об изменениях в тесте
                                subject = f"Изменены параметры Теста: '{test['test_name']}'"
                                message = f"<p style='font-size: 25px;'><b>Уважаемый, {user_object.profile.first_name} {user_object.profile.middle_name}.</b></p><br>" \
                                          f"<p style='font-size: 20px;'>В тест: <b>'{test['test_name']}'</b> внесены следующие изменения:</p>" \
                                          f"<p style='font-size: 20px;'>{info_text}</p>" \
                                          f"<p style='font-size: 20px;'>На портале <a href='{config('SITE_URL', default='')}'>Pilot Test</a></p>" \
                                          f"<br>" \
                                          f"<br>" \
                                          f"<p style='font-size: 20px;'>По умолчанию логин для входа: Ваш email до знака @, пароль такой же</p>" \
                                          f"<p style='font-size: 20px;'>Рекомендуем сменить пароль после первого входа</p>"

                                email_msg = {'subject': subject, 'message': message, 'to': user_object.email}
                                send_email(request, email_msg)

                            instance.num_try = test['num_try']
                            instance.date_before = test['date_before']
                            instance.num_try_initial = test['num_try']
                            instance.save()
                            now = datetime.datetime.now().date()
                            five_day_before = datetime.datetime.now().date() + datetime.timedelta(
                                days=common.days_left_notify)
                            days_left = (test['date_before'].date() - now).days
                            # Если новая дата теста больше сегодняшней, то удалям тест из просроченных у пользователя
                            if test['date_before'].date() > five_day_before:
                                try:
                                    user_test_instance = UserTests.objects.get(user=user_object,
                                                                               test_name=test['test_name'])
                                    TestExpired.objects.get(user=user_object, test=user_test_instance).delete()
                                except Exception:
                                    pass
                            # Если новая дата меньше срока определённого для информирования но больше сегодняшней
                            elif test['date_before'].date() > now:
                                user_test_instance = UserTests.objects.get(user=user_object,
                                                                           test_name=test['test_name'])
                                try:
                                    if TestExpired.objects.get(user=user_object, test=user_test_instance):
                                        user_test_instance = UserTests.objects.get(user=user_object,
                                                                                   test_name=test['test_name'])
                                        tets_inst = TestExpired.objects.get(user=user_object, test=user_test_instance)
                                        tets_inst.days_left = days_left
                                        tets_inst.save()
                                except Exception:
                                    TestExpired.objects.create(user=user_object,
                                                               test=user_test_instance,
                                                               days_left=days_left
                                                               )

                            # UserTests.objects.filter(user=id, test_name=test['test_name']).delete()
                    except Exception:
                        # Создаём только те объекты, которые не помечены для удаления
                        if not test['DELETE']:
                            UserTests.objects.create(user=user_object,
                                                     test_name=test['test_name'],
                                                     num_try_initial=test['num_try'],
                                                     num_try=test['num_try'],
                                                     date_before=test['date_before'])
                            # Записываем журнал, для просмотра пользователем
                            UserChangeLog.objects.create(user_changed=user_object,
                                                         description="Назначен тест",
                                                         test_id=test['test_name'].id,
                                                         test_name=test["test_name"],
                                                         test_date_due=test['date_before'],
                                                         user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                         )
                            logger_user_action.warning(f'Пользователю: '
                                                       f'<b>{user_object.profile.family_name} '
                                                       f'{user_object.profile.first_name[0]}.'
                                                       f'{user_object.profile.middle_name[0]}.</b>\n'
                                                       f'Назначен Тест: <b>{test["test_name"]}</b>\n'
                                                       f'Количество попыток: <b>{test["num_try"]}</b>\n'
                                                       f'Выполнить до: <b>{test["date_before"]}</b>\n\n'
                                                       f'<b>User: </b>{request.user.profile.family_name}'
                                                       f' {request.user.profile.first_name[0]}.'
                                                       f'{request.user.profile.middle_name[0]}.')

                            #  Отправляем письмо пользователю о назначенном тесте
                            subject = f"Вам назначен Тест: '{test['test_name']}'"
                            message = f"<p style='font-size: 25px;'><b>Уважаемый, {user_object.profile.first_name} {user_object.profile.middle_name}.</b></p><br>" \
                                      f"<p style='font-size: 20px;'>Вам назначен тест: <b>'{test['test_name']}'</b></p>" \
                                      f"<p style='font-size: 20px;'>На портале <a href='{config('SITE_URL', default='')}'>Pilot Test</a></p>" \
                                      f"<p style='font-size: 20px;'>Тест необходимо выполнить до <b>{test['date_before'].strftime('%d.%m.%Y')}</b></p>" \
                                      f"<br>" \
                                      f"<p style='font-size: 20px;'>По умолчанию логин для входа: Ваш email до знака @, пароль такой же</p>" \
                                      f"<p style='font-size: 20px;'>Рекомендуем сменить пароль после первого входа</p>"

                            email_msg = {'subject': subject, 'message': message, 'to': user_object.email}
                            send_email(request, email_msg)

            # Загружаем новые данные в форму
            user_tests = UserTests.objects.filter(user=id).values('test_name', 'num_try', 'date_before', 'id')

            tests_for_user_form = UserTestForm(initial=user_tests)
            context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form, 'test_and_data_saved': True,
                       'user_id': id, 'previous_url': previous_url}

            # # Возвращаем пользователя на исходную страницу
            # previous_url = request.POST.get('previous_url', '/')

            # return HttpResponseRedirect(previous_url)
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
                       'form_errors': form_errors, 'user_id': id, 'previous_url': previous_url}
            return render(request, 'user_ditales.html', context=context)
    else:
        user_tests = UserTests.objects.filter(user=id).values('id', 'test_name', 'num_try', 'date_before')
        tests_for_user_form = UserTestForm(initial=user_tests)
        #  Вынимаем и сохраняем адрес страницы, с которой пришёл пользователь
        previous_url = request.META.get('HTTP_REFERER')

        context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form, 'user_id': id,
                   'previous_url': previous_url}
        return render(request, 'user_ditales.html', context=context)


# Создание нового пользователя
@login_required
@group_required('KRS')
def new_user(request):
    form_user = UserRegisterForm()
    form_profile = ProfileForm()
    if request.method == 'POST':

        try:  # Проверяем существование пользователя, если существует, то активируем
            user_obj = User.objects.get(username=request.POST.get('username'))
            if user_obj.is_active:  # Если пользователь существует и активен
                form_user = UserRegisterForm(request.POST)
                form_profile = ProfileForm(request.POST)
                if form_user.is_valid() and form_profile.is_valid():
                    group = Group.objects.get(name=form_profile.cleaned_data[
                                                       'position'] + ' ' + form_profile.cleaned_data[
                                                       'ac_type'])
                    new_user = form_user.save(commit=False)
                    new_user.set_password(form_user.cleaned_data['password1'])
                    new_user.first_name = form_profile.cleaned_data['first_name']
                    new_user.last_name = form_profile.cleaned_data['family_name']
                    new_user.save()
                    new_user.groups.add(group)
                    Profile.objects.create(
                        user=new_user,
                        family_name=form_profile.cleaned_data['family_name'],
                        first_name=form_profile.cleaned_data['first_name'],
                        middle_name=form_profile.cleaned_data['middle_name'],
                        position=form_profile.cleaned_data['position'],
                        ac_type=form_profile.cleaned_data['ac_type']
                        # - Раскоментить на странице new_user.html возможность выбора типа ВС и в forms раскоментить поле ac_type
                    )

                    logger_user_action.warning(f'Создан Пользователь: '
                                               f'<b>{form_profile.cleaned_data["family_name"]} '
                                               f'{form_profile.cleaned_data["first_name"][0]}.'
                                               f'{form_profile.cleaned_data["middle_name"][0]}.</b>\n'
                                               f'Квалификация: <b>{form_profile.cleaned_data["position"]}</b>\n'
                                               f'Тип ВС: <b>{form_profile.cleaned_data["ac_type"]}</b>\n\n'
                                               f'<b>User: </b>{request.user.profile.family_name}'
                                               f' {request.user.profile.first_name[0]}.'
                                               f'{request.user.profile.middle_name[0]}.')
                    UserChangeLog.objects.create(user_changed=new_user,
                                                 description="Добавлен Пилот",
                                                 user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                 )
                    return redirect('quize737:user_list')

                else:
                    context = {'form_user': form_user, 'form_profile': form_profile}
                    return render(request, 'new_user.html', context=context)

            else:  # Если пользователь существует и не активен, активируем
                user_obj.is_active = True
                user_obj.save()
                UserChangeLog.objects.create(user_changed=user_obj,
                                             description="Добавлен Пилот",
                                             user_done=f'{request.user.profile.family_name}'
                                                       f'{request.user.profile.first_name[0]}.'
                                                       f'{request.user.profile.middle_name[0]}.'
                                             )
                return redirect('quize737:user_list')
        except:
            form_user = UserRegisterForm(request.POST)
            form_profile = ProfileForm(request.POST)
            if form_user.is_valid() and form_profile.is_valid():
                group = Group.objects.get(name=form_profile.cleaned_data[
                                                   'position'] + ' ' + form_profile.cleaned_data[
                                                   'ac_type'])
                new_user = form_user.save(commit=False)
                new_user.set_password(form_user.cleaned_data['password1'])
                new_user.first_name = form_profile.cleaned_data['first_name']
                new_user.last_name = form_profile.cleaned_data['family_name']
                new_user.save()
                new_user.groups.add(group)
                Profile.objects.create(
                    user=new_user,
                    family_name=form_profile.cleaned_data['family_name'],
                    first_name=form_profile.cleaned_data['first_name'],
                    middle_name=form_profile.cleaned_data['middle_name'],
                    position=form_profile.cleaned_data['position'],
                    ac_type=form_profile.cleaned_data['ac_type']
                    # - Раскоментить на странице new_user.html возможность выбора типа ВС и в forms раскоментить поле ac_type
                )

                logger_user_action.warning(f'Создан Пользователь: '
                                           f'<b>{form_profile.cleaned_data["family_name"]} '
                                           f'{form_profile.cleaned_data["first_name"][0]}.'
                                           f'{form_profile.cleaned_data["middle_name"][0]}.</b>\n'
                                           f'Квалификация: <b>{form_profile.cleaned_data["position"]}</b>\n'
                                           f'Тип ВС: <b>{form_profile.cleaned_data["ac_type"]}</b>\n\n'
                                           f'<b>User: </b>{request.user.profile.family_name}'
                                           f' {request.user.profile.first_name[0]}.'
                                           f'{request.user.profile.middle_name[0]}.')
                UserChangeLog.objects.create(user_changed=new_user,
                                             description="Добавлен Пилот",
                                             user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                             )
                return redirect('quize737:user_list')

            else:
                context = {'form_user': form_user, 'form_profile': form_profile}
                return render(request, 'new_user.html', context=context)
    else:
        context = {'form_profile': form_profile, 'form_user': form_user}
        return render(request, 'new_user.html', context=context)


# Удаление пользователя
@login_required
@group_required('KRS')
def del_user(request, id):
    user_object = User.objects.get(id=id)
    logger_user_action.warning(f'Удалён Пользователь: '
                               f'<b>{user_object.profile.family_name} '
                               f'{user_object.profile.first_name[0]}.'
                               f'{user_object.profile.middle_name[0]}.</b>\n'
                               f'Квалификация: <b>{user_object.profile.position}</b>\n'
                               f'Тип ВС: <b>{user_object.profile.ac_type}</b>\n\n'
                               f'<b>User: </b>{request.user.profile.family_name}'
                               f' {request.user.profile.first_name[0]}.'
                               f'{request.user.profile.middle_name[0]}.')
    UserChangeLog.objects.create(user_changed=user_object,
                                 description="Удалён Пилот",
                                 user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                 )

    user_object.is_active = False
    user_object.save()
    # user_object.delete()
    # User.objects.get(id=id).delete()
    previous_url = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(previous_url)
    # return redirect('quize737:user_list')


@login_required
@group_required(('KRS', 'Редактор'))
#  Загрузка файла с вопросами
def file_upload(request):
    upload_form = FileUploadForm()
    if request.method == 'POST':

        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            #  Зашружаем файл
            # Ошибка в имени файла, решается так:
            #  https://itekblog.com/ascii-codec-cant-encode-characters-in-position/
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
            f = request.FILES['docfile']
            forman_index = str(f).find('.')
            file_format = str(f)[forman_index:]
            if str(file_format) == '.csv':
                filename = force_str(f).strip().replace(' ', '_')
                filename = force_str(filename).strip().replace('(', '')
                filename = force_str(filename).strip().replace(')', '')

                try:
                    with open(f"{dir_path}/media/documents/{filename}", newline='',
                              encoding='utf-8') as csvfile:

                        #  Пропускаем первую строку (заголовок)
                        try:
                            heading = next(csvfile)
                            fieldnames = ['theme', 'question', 'option_1', 'option_2', 'option_3', 'option_4',
                                          'option_5',
                                          'option_6', 'option_7', 'option_8', 'option_9', 'option_10', 'q_kind',
                                          'q_weight', 'answer', 'answers', 'ac_type']
                            reader = csv.DictReader(csvfile, dialect='excel', fieldnames=fieldnames, delimiter=';')
                        except BaseException as error:

                            wrong_data = ['Вероятно ошибка кодлировки файла, файл должен быть в колировке UTF-8']
                            error_read = error
                            context = {"upload_form": upload_form, 'reading_errors': error_read,
                                       'them_num_created': them_created,
                                       'q_num_created': questions_created, 'uploaded': False, 'wrong_data': wrong_data}
                            return render(request, 'file_upload.html', context=context)
                        try:
                            for row in reader:
                                if row['theme'] and row['question'] and row['option_1'] and row['option_2'] and row[
                                    'q_kind']:
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
                                        if not QuestionSet.objects.filter(Q(question__icontains=row['question'])):
                                            try:
                                                question = QuestionSet.objects.get_or_create(them_name=them[0],
                                                                                             question=row['question'],
                                                                                             option_1=row['option_1'],
                                                                                             option_2=row['option_2'],
                                                                                             option_3=row['option_3'],
                                                                                             option_4=row['option_4'],
                                                                                             option_5=row['option_5'],
                                                                                             option_6=row['option_6'],
                                                                                             option_7=row['option_7'],
                                                                                             option_8=row['option_8'],
                                                                                             option_9=row['option_9'],
                                                                                             option_10=row['option_10'],
                                                                                             q_kind=q_kind,
                                                                                             q_weight=q_weight,
                                                                                             answer=answer,
                                                                                             answers=answers,
                                                                                             ac_type=row['ac_type']
                                                                                             )
                                            except ValueError as error:
                                                wrong_data.append(
                                                    f'Не верные данные в строке {reader.line_num}\n{error}')
                                                continue

                                            if question[1]:
                                                questions_created += 1
                                        # else:

                                        # Подсчитываем созданные вопросы



                                    else:
                                        wrong_data.append(f'Не заполненные поля в строке {reader.line_num}')
                                        continue

                                else:
                                    for data in row.values():
                                        alpha = False
                                        if data is not None:
                                            if data:
                                                if re.search('[a-zA-Z]', str(data)):

                                                    alpha = True
                                                    break
                                                elif re.search('[0-9]', str(data)):

                                                    alpha = True
                                                    break

                                    if alpha == True:
                                        wrong_data.append(f'Не заполненные поля в строке {reader.line_num}')

                                        continue

                        except csv.Error as e:
                            error_read = {'file': filename, 'line': reader.line_num, 'error': e}
                            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
                    os.remove(f"{dir_path}/media/documents/{filename}")

                    context = {"upload_form": upload_form, 'reading_errors': error_read,
                               'them_num_created': them_created,
                               'q_num_created': questions_created, 'uploaded': True, 'wrong_data': wrong_data}
                    return render(request, 'file_upload.html', context=context)
                except IOError as error:
                    wrong_data = ['Неверное имя файла. Попробуйте удалить не стандартные символы в имени файла']
                    # error_read = error
                    context = {"upload_form": upload_form, 'reading_errors': error_read,
                               'them_num_created': them_created,
                               'q_num_created': questions_created, 'uploaded': False, 'wrong_data': wrong_data}
                    return render(request, 'file_upload.html', context=context)


            else:
                filename = force_str(f).strip().replace(' ', '_')
                filename = filename.replace('(', '')
                filename = filename.replace(')', '')
                os.remove(f"{dir_path}/media/documents/{filename}")
                wrong_data = [f'Файл должен быть формата .csv. Формат {file_format} не подходит']
                context = {"upload_form": upload_form, 'uploaded': False, 'wrong_data': wrong_data}
                return render(request, 'file_upload.html', context=context)

    else:
        context = {"upload_form": upload_form, 'uploaded': False}
        return render(request, 'file_upload.html', context=context)


@login_required
@group_required(('KRS', 'Редактор'))
#  Загрузка картинок к вопросам
def all_img_for_q_upload(request, id):
    q_instance = ''
    try:
        q_instance = QuestionSet.objects.get(id=id)
    except ObjectDoesNotExist:
        pass

    if 'delIMG' in request.POST:  # Запрос на удаление картинки
        dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        del_value = request.POST.get('delIMG')
        if del_value == 'DelQIMG':  # Если надо удалить картинку вопроса
            # Удаляем файл
            filelist = glob.glob(f"{dir_path}/media/images/{q_instance.them_name}/{q_instance.id}/q_img.*")
            if filelist:
                for file in filelist:
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            # Удаляем запись в объекте вопроса
            q_instance.question_img = None
            q_instance.save()
            return HttpResponse(status=200)
        else:  # Если надо удалить картинку ответа
            # Удаляем файл
            filelist = glob.glob(f"{dir_path}/media/images/{q_instance.them_name}/{q_instance.id}/a_img.*")
            if filelist:
                for file in filelist:
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            # Удаляем запись в объекте вопроса
            q_instance.comment_img = None
            q_instance.save()
            return HttpResponse(status=200)

    elif 'new_q' in request.POST:  # Если запрос со страницы с новым вопросом
        dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if 'comment_img' in request.FILES:
            file = request.FILES['comment_img']
        else:
            file = request.FILES['question_img']
        fs = FileSystemStorage(location=f"{dir_path}/media/images/tmp", base_url="/media/images/tmp")
        file = fs.save(file.name, file)
        fileurl = fs.url(file)
        return HttpResponse(status=200, content={fileurl})
    else:
        form = IMGform(request.POST, request.FILES, instance=q_instance)
        if form.is_valid():
            # Проверяем существует ли файл
            dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            filelist = []
            if 'question_img' in request.FILES:
                filelist = glob.glob(f"{dir_path}/media/images/{q_instance.them_name}/{q_instance.id}/q_img.*")
            else:
                filelist = glob.glob(f"{dir_path}/media/images/{q_instance.them_name}/{q_instance.id}/a_img.*")
            if filelist:
                for file in filelist:
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            # file = request.FILES['comment_img'].name.split('.')[0]

            # file = request.FILES['question_img']
            # ext = file.name.split('.')[-1]
            # q_instance = QuestionSet.objcts.get(id=id)
            # q_instance.question_img = file(f'q_img.{ext}')

            form.save()
            if 'question_img' in request.FILES:  # Если это картинка для вопроса

                return HttpResponse(status=200, headers={'id': id}, content={q_instance.question_img.url})
            else:  # Если это картинка для ответа
                return HttpResponse(status=200, headers={'id': id}, content={q_instance.comment_img.url})
        else:

            err_list = ''
            for error in form.errors.get_json_data().values():
                err_list = err_list + f'\n{error[0]["message"]}'

            return HttpResponse(status=500, content={err_list})


# Скачивание формы для заполнения вопросов
@login_required
@group_required(('KRS', 'Редактор'))
def question_form_file_download(request):
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path_to_file = dir_path + '/static/PilotTest.xlsx'
    f = open(path_to_file, 'rb')
    return FileResponse(f, as_attachment=True, filename='PilotTest.xlsx')


# Скачивание базы вопросов
@login_required
@group_required(('KRS'))
def download_questions_bay(request):
    constract_mess = 'Функция в разработке'
    context = {'mess': constract_mess}
    return render(request, 'download_questions_bay.html', context=context)


# Сообщение об ошибке в вопросе от пользователя, сообщение рассылается всем пользователям в группе 'Редактор Вопросов'
@login_required
def issue_mess(request, id):
    if 'issue_q_id' in request.GET:
        # if request.method == "POST":
        # form = QuestionIssueMess(request.POST)
        form = QuestionIssueMess(request.GET)
        description = request.GET.get('message')
        # description = request.POST.get('message')
        if form.is_valid():
            q_id = int(request.GET.get('issue_q_id'))
            # q_id = int(request.POST.get('issue_q_id'))
            site_url = config('SITE_URL', default='')
            q_instance = QuestionSet.objects.get(id=q_id)
            q_instance.is_active = False  # Деактивируем вопрос
            q_instance.save()
            ac_type = q_instance.ac_type
            if ac_type != 'ANY':
                emails = User.objects.filter(groups__name='Редактор', profile__ac_type=ac_type).values('email')
            else:
                emails = User.objects.filter(groups__name='Редактор').values('email')
            to = []  # Список email адресов для рассылки
            for email in emails:
                to.append(email['email'])
            subject = f'Ошибка в Вопросе'
            message = f'<p style="font-size: 20px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
                      f'<p style="font-size: 15px;"><b>Сообщил об ошибке в вопросе:</b></p>' \
                      f'<p style="font-size: 15px;"><b>{q_instance.question}</b></p>' \
                      f'<p style="font-size: 15px;"><b>Сообщение пользователя:</b></p>' \
                      f'<p style="font-size: 15px;">{description}</p>' \
                      f'<a href="{site_url}/question_list/{q_id}">Редактировать вопрос</a>'
            email_msg = {'subject': subject, 'message': message, 'to': to}
            common.send_email(request, email_msg)

            return HttpResponse(status=206, headers={'id': id}, content={'test': 'ОТВЕТ'})

        else:
            form = QuestionIssueMess()
            context = {'form': form, 'question_id': id}
            return render(request, 'q_error_mess.html', context=context)

    else:
        form = QuestionIssueMess()
        context = {'form': form, 'question_id': id}
        return render(request, 'q_error_mess.html', context=context)


# Комментарий/пояснение под ответом на вопрос, при просмотре ответов
@login_required
def show_comment(request, id):
    q_instance = QuestionSet.objects.get(id=id)
    context = {'q_instance': q_instance}
    return render(request, 'show_comment.html', context=context)


#  Функция кнопки возврата, с учётом результатов поиска или фильтрации
@login_required
def go_back_button(request):
    # Возвращаем пользователя на исходную страницу
    previous_url = request.GET.get('previous_url', '/')
    #  Вынимаем чистый хост
    # request_host = request.get_host()
    # index = (request.get_host()).find(':')
    # request_host = request_host[:index]
    # if previous_url and urlparse(previous_url).hostname == request_host:

    return HttpResponseRedirect(previous_url)
    # else:
    #     return redirect('/')


# Отправка сообщения администратору
@login_required
def mess_to_admin(request):
    if request.method == "POST":
        form = AdminMessForm(request.POST)
        mess_subject = request.POST.get('subject')
        message = request.POST.get('message')
        if form.is_valid():
            to = common.admin_email
            subject = f'Сообщение Админу Pilot Test'
            message = f'<p style="font-size: 20px;">Сообщение от:</p>' \
                      f'<span style="font-size: 18px;"><b>{request.user.profile.position} </b></span>' \
                      f'<span style="font-size: 18px;"><b>{request.user.profile.ac_type}</b></span>' \
                      f'<p style="font-size: 18px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
                      f'<p style="font-size: 20px;"><b>Тема сообщения:</b></p>' \
                      f'<p style="font-size: 18px;">{mess_subject}</p>' \
                      f'<p style="font-size: 20px;"><b>Сообщение:</b></p>' \
                      f'<p style="font-size: 18px;">{message}</p><br>' \
                      f'<a href="mailto:{request.user.email}">Ответить</a>'
            email_msg = {'subject': subject, 'message': message, 'to': to}
            common.send_email(request, email_msg)
            return HttpResponse(status=204)
        else:

            form = AdminMessForm()
            context = {'form': form}
            return render(request, 'admin_mess.html', context=context)
    else:
        form = AdminMessForm()
        context = {'form': form}
        return render(request, 'admin_mess.html', context=context)


#  Назначение теста произвольной группе пользователей выбранных из общего списка пользователей
@login_required
def selected_users_test(request):
    #  Формируем формы для назначения тестов
    UserTestForm = formset_factory(TestsForUser, extra=0, formset=BaseUserTestFormSet,
                                   can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        previous_url = request.POST.get('previous_url')  # Вынимаем ссылку на изначальную страницу
        selected_users_ids = request.POST.getlist('user_selected')  # ID выбраных пользователей
        total_user_list = []  # Список пользователей, которым надо назначить тест
        # Формируем список объектов пользователей из списка id пользователей
        for user_id in selected_users_ids:
            user_selected = User.objects.get(id=user_id)
            total_user_list.append(user_selected)

        tests_for_group_form = UserTestForm(request.POST,
                                            request.FILES)  # Вынимаем данные из запроса и заполняем ими форму
        if tests_for_group_form.is_valid():
            for test in tests_for_group_form.cleaned_data:
                #  Удаляем все объекты
                # Проверяем было ли указано имя объекта
                # try:
                #     if UserTests.objects.get(test_name=test['test_name']):
                #         UserTests.objects.filter(test_name=test['test_name']).delete()
                # except Exception:
                #     pass
                # Создаём только те объекты, которые не помечены для удаления
                if not test['DELETE']:
                    #  Перебираем всех выбранных пользователей
                    for user in total_user_list:
                        # Проверяем есть ли у пользователя этот тест
                        try:
                            user_test_exists = UserTests.objects.get(user=user, test_name=test['test_name'])
                        except UserTests.DoesNotExist:
                            user_test_exists = None
                        if user_test_exists is None:
                            UserTests.objects.create(user=user,
                                                     test_name=test['test_name'],
                                                     num_try_initial=test['num_try'],
                                                     num_try=test['num_try'],
                                                     date_before=test['date_before'])
                            # Записываем журнал, для просмотра пользователем
                            UserChangeLog.objects.create(user_changed=user,
                                                         description="Назначен тест",
                                                         test_id=test['test_name'].id,
                                                         test_name=test["test_name"],
                                                         test_date_due=test['date_before'],
                                                         user_done=f'{request.user.profile.family_name} {request.user.profile.first_name[0]}.{request.user.profile.middle_name[0]}.'
                                                         )

                            logger_user_action.warning(f'Пользователю: '
                                                       f'<b>{user.profile.family_name} '
                                                       f'{user.profile.first_name[0]}.'
                                                       f'{user.profile.middle_name[0]}.</b>\n'
                                                       f'Назначен Тест: <b>{test["test_name"]}</b>\n'
                                                       f'Количество попыток: <b>{test["num_try"]}</b>\n'
                                                       f'Выполнить до: <b>{test["date_before"]}</b>\n\n'
                                                       f'<b>User: </b>{request.user.profile.family_name}'
                                                       f' {request.user.profile.first_name[0]}.'
                                                       f'{request.user.profile.middle_name[0]}.')
                            #  Отправляем письмо пользователю о назначенном тесте
                            subject = f"Вам назначен Тест: '{test['test_name']}'"
                            message = f"<p style='font-size: 25px;'><b>Уважаемый, {user.profile.first_name} {user.profile.middle_name}.</b></p><br>" \
                                      f"<p style='font-size: 20px;'>Вам назначен тест: <b>'{test['test_name']}'</b></p>" \
                                      f"<p style='font-size: 20px;'>На портале {config('SITE_URL', default='')}</p>" \
                                      f"<p style='font-size: 20px;'>Тест необходимо выполнить до <b>{test['date_before'].strftime('%d.%m.%Y')}</b></p>"

                            email_msg = {'subject': subject, 'message': message, 'to': user.email}
                            send_email(request, email_msg)

            # Загружаем новые данные в форму
            # user_tests = UserTests.objects.filter(user=id).values('test_name', 'num_try', 'date_before')
            # tests_for_user_form = UserTestForm(initial=user_tests)
            # context = {'group': group, 'test_and_data_saved': True}
            # return render(request, 'group_details.html', context=context)
            return redirect('quize737:user_list')

        else:
            form_errors = []  # Ошибки при валидации формы
            for error in tests_for_group_form.errors:
                if len(error) > 0:
                    for value in error.values():
                        form_errors.append(value)
            errors_non_form = tests_for_group_form.non_form_errors
            context = {'selected_user_list': total_user_list, 'group_tests': tests_for_group_form,
                       'non_form_errors': errors_non_form,
                       'form_errors': form_errors, 'previous_url': previous_url}
            return render(request, 'selected_users_test.html', context=context)
    else:
        # Формируем ссылку для кнопки "Вернуться"
        previous_url = '?' + request.META.get('QUERY_STRING')
        selected_user_list = []  # Список пользователей, которые были отмечены

        selected_users_ids = request.GET.getlist('user_selected')
        for user_id in selected_users_ids:
            user_selected = User.objects.get(id=user_id)
            selected_user_list.append(user_selected)

        tests_for_group_form = UserTestForm()  # Формируем изначальную форму
        context = {'selected_user_list': selected_user_list, 'group_tests': tests_for_group_form,
                   'previous_url': previous_url}

        return render(request, 'selected_users_test.html', context=context)


# Создание новой группы с пользователями выбранными из общего списка пользователей
@login_required
def selected_users_new_group(request):
    if request.method == 'POST':
        group_form = GroupForm(request.POST)
        previous_url = request.POST.get('previous_url')  # Вынимаем ссылку на изначальную страницу
        selected_users_ids = request.POST.getlist('user_selected')  # ID выбраных пользователей
        total_user_list = []  # Список пользователей, которым надо назначить тест
        # Формируем список объектов пользователей из списка id пользователей
        for user_id in selected_users_ids:
            user_selected = User.objects.get(id=user_id)
            total_user_list.append(user_selected)
        if group_form.is_valid():
            #  Создаём группу
            group = Group.objects.create(name=group_form.cleaned_data.get('group_name'))  # Добавить группу разрешений
            logger_user_action.warning(f'<b>Создана Группа: </b>{group.name}\n\n'
                                       f'<b>User:</b> {request.user.profile.family_name}'
                                       f' {request.user.profile.first_name[0]}.'
                                       f'{request.user.profile.middle_name[0]}.')
            #  Добавляем группе описание
            GroupsDescription.objects.create(group=group, discription=group_form.cleaned_data.get('discription'))
            # Добаляем пользователей в группу
            for user in total_user_list:
                user.groups.add(group)
            # Возвращаем пользователя на страницу с группами
            return redirect('quize737:group_list')
        else:
            context = {'selected_user_list': total_user_list, 'previous_url': previous_url, 'form': group_form}
            return render(request, 'selected_users_new_group.html', context=context)

    else:
        # Формируем ссылку для кнопки "Вернуться"
        previous_url = '?' + request.META.get('QUERY_STRING')
        selected_user_list = []  # Список пользователей, которые были отмечены

        selected_users_ids = request.GET.getlist('user_selected')
        for user_id in selected_users_ids:
            user_selected = User.objects.get(id=user_id)
            selected_user_list.append(user_selected)

        group_form = GroupForm()
        context = {'selected_user_list': selected_user_list,
                   'previous_url': previous_url, 'form': group_form}

        return render(request, 'selected_users_new_group.html', context=context)


# Добавление в существующую(щие) группу(ы) пользователей выбранных из общего списка пользователей
@login_required
def selected_users_add_to_group(request):
    if request.method == 'POST':
        selected_user_list = []
        selected_groups = request.POST.getlist('group_selected')
        selected_users_ids = request.POST.getlist('user_selected')
        for user_id in selected_users_ids:
            user_selected = User.objects.get(id=user_id)
            selected_user_list.append(user_selected)
        for user in selected_user_list:
            for group in selected_groups:
                user.groups.add(group)
        return redirect('quize737:group_list')

    else:
        groups = Group.objects.all()
        # Формируем ссылку для кнопки "Вернуться"
        previous_url = '?' + request.META.get('QUERY_STRING')
        selected_user_list = []  # Список пользователей, которые были отмечены

        selected_users_ids = request.GET.getlist('user_selected')
        for user_id in selected_users_ids:
            user_selected = User.objects.get(id=user_id)
            selected_user_list.append(user_selected)
        context = {'selected_user_list': selected_user_list,
                   'previous_url': previous_url, 'groups': groups}

        return render(request, 'selected_users_add_to_group.html', context=context)
