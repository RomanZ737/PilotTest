# -*- coding: utf-8 -*-

import os
import random
import io
import csv
import re
import sys

import common

from django.utils.encoding import force_str
from django.core.exceptions import ObjectDoesNotExist
from common import send_email
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
from django.contrib.auth.models import User, Group
from users.models import Profile
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.forms import formset_factory, BaseFormSet
from django.templatetags.static import static
from django.core.exceptions import PermissionDenied
from django.utils import six
from django.db.models import Q
from django.shortcuts import render, redirect
from .models import QuestionSet, Thems, TestQuestionsBay, TestConstructor, QuizeSet, QuizeResults, FileUpload, \
    AnswersResults
from django.contrib.auth.decorators import login_required, user_passes_test
import datetime
from .forms import QuestionSetForm, NewQuestionSetForm, NewTestFormName, NewTestFormQuestions, FileUploadForm, \
    NewThemeForm, MyNewTestFormQuestions
from users.forms import TestsForUser, GroupForm, EditUserForm, ProfileForm, UserRegisterForm, EditGroupForm
from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics  # Библиотека для формирования pdf файла
from reportlab.lib.units import inch  # Библиотека для формирования pdf файла
from reportlab.pdfbase.ttfonts import TTFont
from users.models import Profile, UserTests, GroupsDescription, TestExpired

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


# Заглавная страница
@login_required  # Только для зарегитсрированных пользователей
def start(request, id=None):
    user_instance = request.user
    if request.method == 'POST':

        user_test = UserTests.objects.get(test_name=id, user=user_instance)  # Объект теста конкретного пользователя
        #  Уменьшаем количество попыток у пользователя
        num_try = user_test.num_try  #  Текущее количество попыток
        num_try -= 1
        user_test.num_try = num_try
        #user_test.update(num_try=num_try)
        user_test.save()

        question_set_id = id  # ID теста (сам тест), назначенного пользователю
        test_instance = TestConstructor.objects.filter(id=question_set_id)

        #  Вынимаем объекты Тема и Вопрос, которые принадлежат данному тесту
        q_sets_instances = TestQuestionsBay.objects.filter(test_id=question_set_id).values('theme', 'q_num')
        total_q_number = 0  # Общее количество вопросов в тесте для пользователя
        all_theme_set = []  # Объекты вопросов для пользователя
        particular_user_questions = []  # Номера вопросов в сформированном для пользоваетля тесте
        # thems_num = Thems.objects.all().count()  # Общее количество тем
        max_score_number = 0  # Максимальное количество баллов по сгенерированным вопросам
        # Перебераем темы вопросов
        for q_set in q_sets_instances:
            # Перебираем темы вопросов, если тема = 5 (Все темы)
            if q_set['theme'] == 5:
                for theme in Thems.objects.all():
                    if theme.name != 'Все темы':
                        quiz_set = QuestionSet.objects.filter(Q(them_name=them.name), (Q(ac_type=test_instance[0].ac_type) | Q(ac_type='ANY')))
                        #quiz_set = QuestionSet.objects.filter(them_name=theme.id)  # Берем все вопросы с Темой
                        quiz_set = random.sample(list(quiz_set), int(
                            q_set['q_num']))  # Выбираем случайные вопросы, в количестве определённом в тесте
                        all_theme_set.append(quiz_set)  # Добавляем выбранные вопросы в список
                        # Считаем количество вопросов
                        total_q_number += int(q_set['q_num'])
            # Сохраняем вопросы для пользователя в базу
            else:
                quiz_set = QuestionSet.objects.filter(Q(them_name=q_set['theme']),
                                                      (Q(ac_type=test_instance[0].ac_type) | Q(ac_type='ANY')))
                #quiz_set = QuestionSet.objects.filter(them_name=q_set['theme'])
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
        question_pisition = particular_user_questions[sequence_number]  # Номер вопроса в списке вопросов пользователя

        # Достаём нужный вопрос из базы вопросов по сквозному номеру
        question = QuestionSet.objects.filter(id=question_pisition).values()
        # Вынимаем объект вопроса
        question_instance = QuestionSet.objects.get(id=question_pisition)

        # Формируем данные для отправки на страницу тестирования

        # Обновляем количество оставшихся вопросов - закоментил т.е. уменьшать количество вопросов надо после ответа пользователя
        #QuizeSet.objects.filter(id=user_quize_set.id).update(q_sequence_num=sequence_number)

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
            pass_score=test_instance[0].pass_score
        )

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
                   'tmp_test_id': user_quize_set.id, 'result_id': result_obj.id, 'option_dict': option_dict,
                   'q_num_left': total_q_number, 'q_instance': question_instance}
        # Проверяем содержит ли вопрос мультивыбор
        if not question[0]['q_kind']:
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
                test_in_progress = QuizeSet.objects.get(test_id=id, user_under_test=request.user.username)  # Объект сформированного пользователю теста
                #  Если сформированный пользователю тест существует, продолжаем выполнение
                in_progress = True #  Флаг не завершунного теста
                test_instance = TestConstructor.objects.get(id=id)  # Объект теста (изначальный)
                user_test = UserTests.objects.filter(test_name=id)  # Объект теста назначенного пользователю
                results_instance = QuizeResults.objects.get(user_id=request.user, quize_name=test_instance.name)  # Сформированный результат выполнения теста
                user_tests = UserTests.objects.filter(user=request.user)  # Весь список тестов пользователя для отображения в боковом меню
                test_question_sets = TestQuestionsBay.objects.filter(test_id=id)  #  Вопросы теста, назначенного пользователю

                #-----------------------------------------------
                # Количество оставшихся у пользователя вопросов
                # q_amount = test_in_progress.q_sequence_num
                # # Номера вопросов сгенерированные пользователю
                # q_num_list = list((test_in_progress.questions_ids).split(' '))
                # # Выясняем ID вопроса по номеру позиции вопроса в списке
                # question_pisition = q_num_list[int(q_amount) - 1]
                # # Достаём нужный вопрос из базы вопросов по сквозному номеру
                # question = QuestionSet.objects.filter(id=question_pisition).values()
                # #  Создаём словарь с вариантами ответов на вопрос
                # option_dict = {}
                # for option_num in range(1, 11):
                #     option_dict[f'option_{option_num}'] = question[0][f'option_{option_num}']
                # -----------------------------------------------

                context = {'question_set': test_question_sets, 'test_name': test_instance, 'user_test': user_test[0],
                           'user_tests': user_tests, 'in_progress': in_progress, 'tmp_test_id':test_in_progress.id, 'result_id': results_instance.id, 'question_id': id}
                return render(request, 'start_test_ditales.html', context=context)

            except ObjectDoesNotExist:
                in_progress = False
                user_test = UserTests.objects.filter(test_name=id)  # Выбраный пользователем тест
                user_tests = UserTests.objects.filter(user=request.user)  # Весь список тестов пользователя для отображения
                test_instance = TestConstructor.objects.get(id=id)
                test_question_sets = TestQuestionsBay.objects.filter(test_id=id)
                context = {'question_set': test_question_sets, 'test_name': test_instance, 'user_test': user_test[0],
                           'user_tests': user_tests, 'in_progress': in_progress}
                return render(request, 'start_test_ditales.html', context=context)
        #  Если пользователь открывает страницу со списком тестов
        else:
            user_tests = UserTests.objects.filter(user=request.user)
            context = {'user_tests': user_tests}
            return render(request, 'start.html', context=context)


@login_required  # Только для зарегитсрированных пользователей
# Генерация последующих вопросов
def next_question(request):
    # Проверяем нажал ли пользователь кнопку "ответить"
    if request.method == 'POST':
        user_quize_set_id = int(request.POST.get('tmp_test_id')) #  ID сформированного пользователю теста, удаляется после завершения теста пользователем (с любым результатом)
        # Количество оставшихся у пользователя вопросов
        q_amount = QuizeSet.objects.filter(id=user_quize_set_id).values('q_sequence_num')
        # Уменьшаем на единицу количество оставшихся вопросов
        question_sequence = int(q_amount[0]['q_sequence_num']) - 1
        # Обновляем количество оставшихся вопросов
        QuizeSet.objects.filter(id=user_quize_set_id).update(q_sequence_num=question_sequence)

        #  Вынимаем объект отвеченного вопроса
        answered_q_instance = QuestionSet.objects.get(id=request.POST.get('question_id'))
        #  Вынимает объект результатов пользователя
        results_inst = QuizeResults.objects.get(id=request.POST.get('result_id'))
        # Проверяем вид вопроса
        #  Если вопрос имеет несколько вариантов ответа
        if answered_q_instance.q_kind:
            # Преобразуем ответы пользователя во множество
            user_answers_set = set()
            for answer in request.POST.getlist('user_answer'):
                user_answers_set.add(int(answer.replace('option_', '')))
            # Вынимаем правильные ответы из вопроса и преобразуем во множество чисел
            correct_answers_set = set(map(int, (answered_q_instance.answers).split(',')))
            # Если ответ пользователя правильный
            if user_answers_set == correct_answers_set:
                #  Создаём объект ответа на вопрос конкретного теста
                AnswersResults.objects.create(user=request.user,
                                              results=results_inst,
                                              question=answered_q_instance,
                                              user_answer=user_answers_set,
                                              conclusion=True
                                              )

                # Вынимаем текущее количество правильных ответов и количество баллов пользователя
                user_result_data = QuizeResults.objects.filter(id=request.POST.get('result_id')).values(
                    'correct_q_num', 'score_number')

                # Увеличиваем количество правильных ответов на единицу и записыввем в базу
                QuizeResults.objects.filter(id=request.POST.get('result_id')).update(
                    correct_q_num=(user_result_data[0]['correct_q_num'] + 1))

                # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть
                print('answered_q_instance.q_weight', answered_q_instance.q_weight)
                if answered_q_instance.q_weight != 0:
                    updated_score_number = user_result_data[0]['score_number'] + answered_q_instance.q_weight
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
        else:
            #  Если вопрос с одним вариантом ответа
            user_aswer = request.POST.get('user_answer').replace('option_', '')
            print('request.POST', request.POST)
            # Если пользователь правильно ответил на вопрос:
            if int(answered_q_instance.answer) == int(user_aswer):
                #  Создаём объект ответа на вопрос конкретного теста
                AnswersResults.objects.create(user=request.user,
                                              results=results_inst,
                                              question=answered_q_instance,
                                              user_answer=user_aswer,
                                              conclusion=True
                                              )
                # Вынимаем текущее количество правильных ответов и количество баллов пользователя
                user_result_data = QuizeResults.objects.filter(id=request.POST.get('result_id')).values(
                    'correct_q_num', 'score_number')

                # Увеличиваем количество правильных ответов на единицу и записыввем в базу
                QuizeResults.objects.filter(id=request.POST.get('result_id')).update(
                    correct_q_num=(user_result_data[0]['correct_q_num'] + 1))

                # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть
                print('answered_q_instance.q_weight', answered_q_instance.q_weight)
                if float(answered_q_instance.q_weight) != 0:
                    updated_score_number = user_result_data[0]['score_number'] + float(answered_q_instance.q_weight)

                else:
                    updated_score_number = user_result_data[0]['score_number'] + 1
                print('updated_score_number', updated_score_number)

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
                print('Не правильный ответ')

        # # Количество оставшихся у пользователя вопросов
        # q_amount = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values('q_sequence_num')

        # Номера вопросов сгенерированные пользователю
        q_num_list = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values('questions_ids')

        # Проверяем остались ли ещё вопросы в тесте пользователя
        if int(q_amount[0]['q_sequence_num']) > 0:
            q_num_list = list((q_num_list[0]['questions_ids']).split(' '))

            # Номер позиции вопроса в списке
            # question_sequence = int(q_amount[0]['q_sequence_num']) - 1
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
                       'option_dict': option_dict, 'q_num_left': q_amount[0]['q_sequence_num'], 'q_instance': question_instance}

            # Формируем данные для отправки на страницу тестирования
            # context = {'user_name': request.POST.get("user_name"), 'user_set_id': request.POST.get('user_set_id'), 'question': question, 'results_object_id': request.POST.get('results_object_id'), 'q_kind': question[0]['q_kind'], 'q_num_left': q_amount[0]['q_sequence_num']}

            # Обновляем количество оставшихся вопросов
            QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).update(q_sequence_num=question_sequence)

            # Проверяем содержит ли вопрос мультивыбор
            if question[0]['q_kind'] == False:
                q_page_layout = 'start_test_radio.html'
            else:
                q_page_layout = 'start_test_check.html'

            return render(request, q_page_layout, context=context)

        else:
            # Ставим флаг завершённости теста
            QuizeResults.objects.filter(id=request.POST.get('result_id')).update(in_progress=False)
            # Вынимаем количество правильных ответов, число вопросов и количество баллов
            result_data = QuizeResults.objects.filter(id=int(request.POST.get('result_id'))).values(
                'correct_q_num', 'score_number', 'total_num_q', 'pass_score')

            # Вынимаем количество максимально возможных баллов
            max_score_num = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).values('max_score_amount')

            # Вычисляем процент прохождения теста и округляем результат до десятой
            total_result = ('%.0f' % ((result_data[0]['score_number'] * 100) / max_score_num[0]['max_score_amount']))

            # Если пользователь сдал тест
            if int(total_result) >= int(result_data[0]['pass_score']):
                #  Вынимаем объект набора вопросов (QuizeSet) для исфользования в фильтре удаления теста польхователя, если он сдал тест
                set_instance = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id')))
                results_instance = QuizeResults.objects.filter(id=int(request.POST.get('result_id')))
                results_instance.update(total_result=total_result, conclusion=True)
                # Вынимаем id теста для удаления теста у пользователя
                user_test_id = set_instance[0].test_id  # ID теста пользователя
                user_test_name = set_instance[0].quize_name  # Название теста пользователя
                #  Удаляем тест у пользователя

                user_test_instance = UserTests.objects.filter(user=request.user, test_name=user_test_id)

                answer_results = []
                answers = AnswersResults.objects.filter(user=results_inst.user_id, results=results_inst)
                #  Формируем список ответов в результатах теста
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
                                    options.append(
                                        {f'option': getattr(question.question, f'option_{i}'), 'valid': False})
                        user_answer = question.user_answer
                        question_block['answers'] = options
                        question_block['user_answer'] = [getattr(question.question, f'option_{user_answer}')]

                    #  Если на вопрос несколько ответов
                    else:
                        options = []
                        #  Список с правильными ответами
                        correct_answers_list = list(map(int, question.question.answers.split(',')))
                        print('correct_answers_list', correct_answers_list)
                        for i in range(1, 11):
                            if i in correct_answers_list:
                                options.append({f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                            else:
                                if getattr(question.question, f'option_{i}'):
                                    options.append(
                                        {f'option': getattr(question.question, f'option_{i}'), 'valid': False})

                        question_block['answers'] = options
                        user_answers = []
                        for number in question.user_answer:
                            if number.isdigit():
                                user_answers.append(number)
                        answer = []
                        for user_answer in user_answers:
                            print('user_answer', user_answer)
                            answer.append(getattr(question.question, f'option_{user_answer}'))
                        question_block['user_answer'] = answer

                    answer_results.append(question_block)

                context = {'user_name': results_instance[0].user_name, 'total_num_q': result_data[0]['total_num_q'],
                           'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result,
                           'conclusion': True, 'answers': answer_results}
                # Удаляем тест пользователя из базы тестов пользователя

                QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).delete()

                # Отправляем письмо КРС если тест не тренировочный
                if user_test_instance[0].test_name.training == False:
                    site_url = config('SITE_URL', default='')
                    subject = f'Пилот {request.user.profile.family_name} {(request.user.profile.first_name)[0]}. {(request.user.profile.middle_name)[0]}. Сдал Тест'
                    message = f'<p style="font-size: 20px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
                              f'<p style="color: rgb(148, 192, 74); font-size: 20px;"><b>СДАЛ ТЕСТ</b></p>' \
                              f'<p style="font-size: 15px;">Название теста: <b>{user_test_name}</b></p>' \
                              f'<p style="font-size: 15px;">Набрано баллов: <b>{total_result}%</b></p>' \
                              f'<p style="font-size: 15px;">Проходной балл: <b>{result_data[0]["pass_score"]}%</b></p>' \
                              f'<a href="{site_url}/tests_results_list/{results_instance[0].id}">Посмотреть подробности</a>'
                    to = common.krs_mail_list
                    email_msg = {'subject': subject, 'message': message, 'to': to}
                    common.send_email(request, email_msg)
                else:
                    # Если тест тренировочный, удаляем результаты теста
                    results_instance.delete()

                #  Удаляем тест у пользователя
                user_test_instance[0].delete()

                return render(request, 'results.html', context=context)

            # Если пользователь тест НЕ сдал
            else:
                results_instance = QuizeResults.objects.filter(id=int(request.POST.get('result_id')))
                set_instance = QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id')))
                user_test_id = set_instance[0].test_id
                user_test_name = set_instance[0].quize_name  # Название теста пользователя
                user_test_instance = UserTests.objects.filter(user=request.user, test_name=user_test_id)
                # Уменьшаем количество попыток
                num_try = user_test_instance[0].num_try
                # num_try -= 1
                # user_test_instance.update(num_try=num_try)

                # Если у пользователя не осталось попыток, отправляем письмо КРС
                if int(num_try) == 0:
                    QuizeResults.objects.filter(id=int(request.POST.get('result_id'))).update(
                        total_result=total_result, conclusion=False)

                    answer_results = []
                    answers = AnswersResults.objects.filter(user=results_inst.user_id, results=results_inst)

                    #  Формируем список ответов в результатах теста
                    for question in answers:
                        question_block = {}
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
                                            {f'option': getattr(question.question, f'option_{i}'), 'valid': False})
                            user_answer = question.user_answer
                            question_block['answers'] = options
                            question_block['user_answer'] = [getattr(question.question, f'option_{user_answer}')]

                        #  Если на вопрос несколько ответов
                        else:
                            options = []
                            #  Список с правильными ответами
                            correct_answers_list = list(map(int, question.question.answers.split(',')))
                            print('correct_answers_list', correct_answers_list)
                            for i in range(1, 11):
                                if i in correct_answers_list:
                                    options.append(
                                        {f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                                else:
                                    if getattr(question.question, f'option_{i}'):
                                        options.append(
                                            {f'option': getattr(question.question, f'option_{i}'), 'valid': False})

                            question_block['answers'] = options
                            user_answers = []
                            for number in question.user_answer:
                                if number.isdigit():
                                    user_answers.append(number)
                            answer = []
                            for user_answer in user_answers:
                                print('user_answer', user_answer)
                                answer.append(getattr(question.question, f'option_{user_answer}'))
                            question_block['user_answer'] = answer

                        answer_results.append(question_block)

                    # Отправляем письмо КРС если тест не тренировочный
                    if user_test_instance[0].test_name.training == False:
                        site_url = config('SITE_URL', default='')
                        subject = f'Пилот {request.user.profile.family_name} {(request.user.profile.first_name)[0]}. {(request.user.profile.middle_name)[0]}. НЕ сдал тест'
                        message = f'<p style="font-size: 20px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
                                  f'<p style="color: rgb(142, 23, 11); font-size: 20px;"><b>НЕ СДАЛ ТЕСТ</b></p>' \
                                  f'<p style="font-size: 15px;">Название теста: <b>{user_test_name}</b></p>' \
                                  f'<p style="font-size: 15px;">Набрано баллов: <b>{total_result}%</b></p>' \
                                  f'<p style="font-size: 15px;">Проходной балл: <b>{result_data[0]["pass_score"]}%</b></p>' \
                                  f'<a href="{site_url}/tests_results_list/{results_instance[0].id}">Посмотреть подробности</a>'
                        to = common.krs_mail_list
                        email_msg = {'subject': subject, 'message': message, 'to': to}
                        common.send_email(request, email_msg)
                    else:
                        # Удаляем результаты теста, если тест тренировояный
                        results_instance.delete()
                    context = {'user_name': results_instance[0].user_name, 'total_num_q': result_data[0]['total_num_q'],
                               'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result,
                               'conclusion': False, 'answers': answer_results}
                    QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).delete()
                    return render(request, 'results.html', context=context)
                else:

                    answer_results = []
                    answers = AnswersResults.objects.filter(user=results_inst.user_id, results=results_inst)

                    #  Формируем список ответов в результатах теста
                    for question in answers:
                        question_block = {}
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
                                            {f'option': getattr(question.question, f'option_{i}'), 'valid': False})
                            user_answer = question.user_answer
                            question_block['answers'] = options
                            question_block['user_answer'] = [getattr(question.question, f'option_{user_answer}')]

                        #  Если на вопрос несколько ответов
                        else:
                            options = []
                            #  Список с правильными ответами
                            correct_answers_list = list(map(int, question.question.answers.split(',')))
                            print('correct_answers_list', correct_answers_list)
                            for i in range(1, 11):
                                if i in correct_answers_list:
                                    options.append(
                                        {f'option': getattr(question.question, f'option_{i}'), 'valid': True})
                                else:
                                    if getattr(question.question, f'option_{i}'):
                                        options.append(
                                            {f'option': getattr(question.question, f'option_{i}'), 'valid': False})

                            question_block['answers'] = options
                            user_answers = []
                            for number in question.user_answer:
                                if number.isdigit():
                                    user_answers.append(number)
                            answer = []
                            for user_answer in user_answers:
                                print('user_answer', user_answer)
                                answer.append(getattr(question.question, f'option_{user_answer}'))
                            question_block['user_answer'] = answer

                        answer_results.append(question_block)

                    context = {'user_name': results_instance[0].user_name, 'total_num_q': result_data[0]['total_num_q'],
                               'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result,
                               'conclusion': False, 'answers': answer_results}

                    QuizeSet.objects.filter(id=int(request.POST.get('tmp_test_id'))).delete()
                    QuizeResults.objects.filter(id=int(request.POST.get('result_id'))).delete()
                    return render(request, 'results.html', context=context)

    #  Если пользователь продолжает попытку
    else:
        user_quize_set_id = int(request.GET.get('tmp_test_id'))  # ID сформированного пользователю теста, удаляется после завершения теста пользователем (с любым результатом)
        # Количество оставшихся у пользователя вопросов
        q_amount = QuizeSet.objects.filter(id=user_quize_set_id).values('q_sequence_num')
        q_num_list = QuizeSet.objects.filter(id=int(request.GET.get('tmp_test_id'))).values('questions_ids')
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
                   'tmp_test_id': request.GET.get('tmp_test_id'), 'result_id': request.GET.get('result_id'),
                   'option_dict': option_dict, 'q_num_left': q_amount[0]['q_sequence_num'],
                   'q_instance': question_instance}

        # Проверяем содержит ли вопрос мультивыбор
        if question[0]['q_kind'] == False:
            q_page_layout = 'start_test_radio.html'
        else:
            q_page_layout = 'start_test_check.html'

        return render(request, q_page_layout, context=context)


@login_required
@group_required('KRS')
# Все результаты тестов
def tests_results_list(request):
    groups = Group.objects.all().values()
    results_list_options = ['ТЕСТ СДАН', 'ТЕСТ НЕ СДАН', 'Все']
    group_list = []
    for group in groups:
        group_list.append(group)
    group_list.append({'name': 'Все'})  # Добавляем выбор всех групп
    position_list = Profile.Position.values
    position_list.append('Все')  # Добавляем вариант выбора всехдолжностей
    user_search_input = request.GET.get("user_search")
    filter_input = request.GET.getlist("filter")
    no_search_result = False
    if user_search_input or filter_input:
        if user_search_input:
            total_results_list = QuizeResults.objects.filter(Q(user_name__icontains=f'{user_search_input}'),
                                                             in_progress=False)
            if not total_results_list:
                no_search_result = True
                results = f'Пилоты по запросу "{user_search_input}" не найдены'
                context = {'no_search_results': no_search_result, 'results': results, 'filter_input': filter_input,
                           'position_list': position_list, 'group_list': group_list,
                           'results_list_options': results_list_options}
                return render(request, 'tests_results_list.html', context=context)
            else:
                paginator = Paginator(total_results_list, 10)
                page_number = request.GET.get('page', 1)
                results_list_pages = paginator.page(page_number)
                context = {'results': results_list_pages, 'no_search_results': no_search_result,
                           'filter_input': filter_input,
                           'position_list': position_list, 'group_list': group_list,
                           'results_list_options': results_list_options}
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
                                                              conclusion__exact=result, in_progress=False).distinct()
            else:
                total_user_list = QuizeResults.objects.filter(user_id__profile__position__icontains=position,
                                                              user_id__groups__name__icontains=group,
                                                              conclusion__icontains=result,
                                                              in_progress=False).distinct()
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
        results_list = QuizeResults.objects.filter(in_progress=False)
        paginator = Paginator(results_list, 10)
        page_number = request.GET.get('page', 1)
        results_list_pages = paginator.page(page_number)
        context = {'results': results_list_pages, 'position_list': position_list, 'group_list': group_list,
                   'results_list_options': results_list_options}
        return render(request, 'tests_results_list.html', context=context)


@login_required
@group_required('KRS')
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
            print('correct_answers_list', correct_answers_list)
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
                print('user_answer', user_answer)
                answer.append(getattr(question.question, f'option_{user_answer}'))
            question_block['user_answer'] = answer

        answer_results.append(question_block)

    context = {'result': result, 'id': id, 'answers': answer_results}
    return render(request, 'test_result_details.html', context=context)


# Список вопросов из базы
@login_required
@group_required(('KRS', 'Редактор'))
def question_list(request):
    them_list = Thems.objects.all()
    user_search_input = request.GET.get("question_search")
    filter_input = request.GET.getlist("filter")
    ac_type_list = QuestionSet.ACType.values  # Создаём список всех типов самолёта
    ac_type_list.append('Все')  # Добавляем вариант "Все"
    print('filter_input', filter_input)

    no_search_result = False
    if user_search_input or filter_input:
        if user_search_input:
            total_questions_list = QuestionSet.objects.filter(Q(question__icontains=f'{user_search_input}'))
            q_count = total_questions_list.count()
            if not total_questions_list:
                no_search_result = True
                results = f'Вопросы по запросу "{user_search_input}" не найдены'
                context = {'no_search_results': no_search_result, 'results': results, 'them_list': them_list,
                           'q_count': q_count}
                return render(request, 'question_list.html', context=context)
            else:
                paginator = Paginator(total_questions_list, 15)
                page_number = request.GET.get('page', 1)
                results_list_pages = paginator.page(page_number)
                context = {'questions': results_list_pages, 'no_search_results': no_search_result,
                           'them_list': them_list, 'q_count': q_count}
                return render(request, 'question_list.html', context=context)
        else:
            them = ''
            ac_type = ''
            if filter_input[0] != 'Все темы':
                them = filter_input[0]
            if filter_input[1] != 'Все':
                ac_type = filter_input[1]

            them_q_list = QuestionSet.objects.filter(them_name__name__icontains=them, ac_type__icontains=ac_type)
            q_count = them_q_list.count()  # Подстчитываем количество вопросов
            paginator = Paginator(them_q_list, 15)
            page_number = request.GET.get('page', 1)
            results_list_pages = paginator.page(page_number)
            context = {'questions': results_list_pages, 'no_search_results': no_search_result,
                       'them_list': them_list, 'filter_input': filter_input, 'q_count': q_count,
                       'ac_type': ac_type_list}
            return render(request, 'question_list.html', context=context)
    else:
        question_list = QuestionSet.objects.all()
        q_count = question_list.count()
        paginator = Paginator(question_list, 15)
        page_number = request.GET.get('page', 1)
        questions = paginator.page(page_number)
        filtered = None
        context = {'questions': questions, 'them_list': them_list, 'filtered': filtered, 'q_count': q_count,
                   'ac_type': ac_type_list}
        return render(request, 'question_list.html', context=context)


# Добавить новый вопрос в базу вопросов
@login_required
@group_required(('KRS', 'Редактор'))
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
@group_required(('KRS', 'Редактор'))
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
                                                          'option_4', 'option_5', 'option_6', 'option_7', 'option_8',
                                                          'option_9', 'option_10', 'q_kind', 'q_weight', 'answer',
                                                          'answers', 'id', 'ac_type')
        question_form = QuestionSetForm(result[0])

        context = {'question_form': question_form, 'q_id': result[0]['id']}

        return render(request, 'question_list_details.html', context=context)


# Удаляем вопрос
@login_required
@group_required(('KRS', 'Редактор'))
def question_del(request, id):
    QuestionSet.objects.get(id=id).delete()
    return redirect('quize737:question_list')


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
            theme_list = Thems.objects.all()
            them_num = Thems.objects.all().count()
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
    print('id:', id)
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
            test_them_num = Thems.objects.all().count()
            users_number = UserTests.objects.filter(
                test_name=test).count()  # Количество пользователей, которым назначен конкретный тест
            q_num = int()
            for q in test_data:
                if q.theme.name == 'Все темы':
                    q_num = (int(test_them_num) - 1) * q.q_num
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
    ac_types_list = Profile.ACType.values  # Список типов ВС для фильтра
    ac_types_list.append('Все')  # Добавляем в выбор вариант 'Все'
    context = {'ac_type': ac_types_list}
    return render(request, 'new_test_ac_type.html', context=context)


@login_required
@group_required('KRS')
def create_new_test(request):
    ac_type = request.GET.get('ac_type')
    thems = Thems.objects.all()
    total_q_num_per_them = {}
    totla_q_num = 0
    min_q_them = []
    all_them_instance = Thems.objects.get(id=5)  # Instance объекта 'Все темы'
    for them_name in thems:
        # Считаем количество вопросов в каждой теме, кроме "Все темы"
        if them_name.id != 5:
            q_num = QuestionSet.objects.filter(Q(them_name=them_name), (Q(ac_type=ac_type) | Q(ac_type='ANY'))).count()
            if q_num > 0:
                total_q_num_per_them[them_name] = q_num
                totla_q_num += 1
                min_q_them.append(q_num)
    min_q_them.sort()
    total_q_num_per_them[all_them_instance] = min_q_them[0]  # Включаем 'Все темы' в список выбора тем
    thems_selection = []
    # Создаём список тем для конктретного типа ВС
    for them in total_q_num_per_them.keys():
        thems_selection.append((them.id, them.name))
    QuestionFormSet = formset_factory(MyNewTestFormQuestions, min_num=1, max_num=20, extra=0, absolute_max=20,
                                      formset=BaseArticleFormSet, can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        ac_type = request.POST.get('ac_type')  # Вынимаем Тип ВС

        print('POST', request.POST)
        test_q_set = QuestionFormSet(request.POST, request.FILES, form_kwargs={'thems_selection': tuple(thems_selection)}, initial=[{'theme': '5', 'q_num': '4'}],
                                     prefix="questions")
        test_name_form = NewTestFormName(request.POST, prefix="test_name")

        if test_q_set.is_valid() and test_name_form.is_valid():
            # Создаём объект теста
            training = False
            if test_name_form.data['test_name-training'] == 'on':
                training = True
            new_test = TestConstructor.objects.create(name=test_name_form.data['test_name-name'],
                                                      pass_score=test_name_form.data['test_name-pass_score'],
                                                      training=training,
                                                      ac_type=ac_type)
            # Создаём объекты вопросов теста

            for question in test_q_set.cleaned_data:
                print('question', question)
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
            print('test_q_set',test_q_set)
            context = {'test_name_form': test_name_form, 'test_q_set': test_q_set, 'non_form_errors': errors_non_form,
                       'form_errors': form_errors, 'q_num_per_them': total_q_num_per_them, 'ac_type': ac_type}
            return render(request, 'new_test_form.html', context=context)
    else:
        # https://translated.turbopages.org/proxy_u/en-ru.ru.9354fe54-64555aae-631f0b43-74722d776562/https/docs.djangoproject.com/en/dev/topics/forms/formsets/#formsets
        test_name_form = NewTestFormName(prefix="test_name")
        test_q_set = QuestionFormSet(form_kwargs={'thems_selection': tuple(thems_selection)}, initial=[{'theme': '5', 'q_num': '4', }], prefix='questions')
        context = {'test_name_form': test_name_form, 'test_q_set': test_q_set, 'q_num_per_them': total_q_num_per_them, 'ac_type': ac_type}
        return render(request, 'new_test_form.html', context=context)


@login_required
@group_required('KRS')
# Редактируем Детали уже существующего конекретного теста
def test_details(request, id):
    # Вынимаем объект теста
    test_instance = TestConstructor.objects.filter(id=id).values('name', 'id', 'pass_score', 'training', 'ac_type')
    ac_type = test_instance[0]['ac_type']
    thems = Thems.objects.all()
    total_q_num_per_them = {}
    totla_q_num = 0
    min_q_them = []
    all_them_instance = Thems.objects.get(id=5)  # Instance объекта 'Все темы'
    for them_name in thems:
        # Считаем количество вопросов в каждой теме, кроме "Все темы"
        if them_name.id != 5:
            q_num = QuestionSet.objects.filter(Q(them_name=them_name), (Q(ac_type=ac_type) | Q(ac_type='ANY'))).count()
            if q_num > 0:
                total_q_num_per_them[them_name] = q_num
                totla_q_num += 1
                min_q_them.append(q_num)
    min_q_them.sort()
    total_q_num_per_them[all_them_instance] = min_q_them[0]  # Включаем 'Все темы' в список выбора тем
    thems_selection = []
    # Создаём список тем для конктретного типа ВС
    for them in total_q_num_per_them.keys():
        thems_selection.append((them.id, them.name))
    #  Формируем форму
    QuestionFormSet = formset_factory(MyNewTestFormQuestions, min_num=1, max_num=10, extra=0, absolute_max=20,
                                      formset=BaseArticleFormSet, can_delete=True)  # Extra - количество строк формы

    if request.method == 'POST':
        a = TestConstructor.objects.get(id=id)
        test_name_form = NewTestFormName(request.POST)
        test_q_set = QuestionFormSet(request.POST, request.FILES, form_kwargs={'thems_selection': tuple(thems_selection)}, prefix="questions")
        TestQuestionsBay.objects.filter(test_id=id).delete()
        if test_q_set.is_valid():
            training = False
            a.name = test_name_form.data.get('name')
            a.pass_score = test_name_form.data.get('pass_score')
            if test_name_form.data.get('training') == 'on':
                training = True
            a.training = training
            a.save()
            for question in test_q_set.cleaned_data:
                if not question['DELETE']:
                    them_instance = Thems.objects.get(id=question['theme'])
                    TestQuestionsBay.objects.create(theme=them_instance,
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
                       'form_errors': form_errors, 'test_id': id, 'ac_type': test_instance[0]['ac_type']}
            return render(request, 'test_detailes.html', context=context)

    else:
        test_name_form = NewTestFormName(test_instance[0])  # Форма с названием теста
        test_questions = TestQuestionsBay.objects.filter(test_id=id).values('theme', 'q_num')
        # Создаём набор форм
        test_q_set = QuestionFormSet(form_kwargs={'thems_selection': tuple(thems_selection)}, initial=test_questions, prefix='questions')
        context = {'test_q_set': test_q_set, 'test_name_form': test_name_form, 'test_id': test_instance[0]['id'],
                   'q_num_per_them': total_q_num_per_them, 'ac_type': test_instance[0]['ac_type']}
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
        position_list = Profile.Position.values
        position_list.append('Все')  # Добавляем вариант выбора всех должностей
        ac_types_list = Profile.ACType.values  # Список типов ВС для фильтра
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
                                                          Q(profile__middle_name__icontains=f'{user_search_data[2]}')).exclude(
                        username='roman')
                elif len(user_search_data) == 2:
                    total_user_list = User.objects.filter(Q(profile__family_name__icontains=f'{user_search_data[0]}'),
                                                          Q(profile__first_name__icontains=f'{user_search_data[1]}')).exclude(
                        username='roman')
                    if not total_user_list:
                        total_user_list = User.objects.filter(
                            Q(profile__first_name__icontains=f'{user_search_data[0]}'),
                            Q(profile__middle_name__icontains=f'{user_search_data[1]}')).exclude(username='roman')
                elif len(user_search_data) == 1:
                    total_user_list = User.objects.filter(
                        Q(profile__family_name__icontains=f'{user_search_data[0]}') | Q(
                            profile__first_name__icontains=f'{user_search_data[0]}') | Q(
                            profile__middle_name__icontains=f'{user_search_data[0]}')).exclude(username='roman')
                else:
                    no_search_result = True
                    results = f'Пилоты по запросу "{user_search_input}" не найдены'
                    context = {'no_search_results': no_search_result, 'results': results,
                               'position_list': position_list, 'group_list': group_list, 'ac_types': ac_types_list}
                    return render(request, 'user_list.html', context=context)
                if not total_user_list:
                    no_search_result = True
                    results = f'Пилоты по запросу "{user_search_input}" не найдены'
                    context = {'no_search_results': no_search_result, 'results': results,
                               'position_list': position_list, 'group_list': group_list,
                               'assign_test_list': assign_test_list}
                    return render(request, 'user_list.html', context=context)
                else:
                    total_user_number = len(total_user_list)
                    paginator = Paginator(total_user_list, 20)
                    page_number = request.GET.get('page', 1)
                    users = paginator.page(page_number)
                    context = {'user_list': users, 'no_search_results': no_search_result,
                               'position_list': position_list, 'group_list': group_list, 'tests_list': test_list,
                               'user_test_dict': user_test_dict, 'user_num': total_user_number}
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
                    test = filter_input[3]
                    total_user_list = User.objects.filter(profile__ac_type__icontains=ac_type, profile__position__icontains=position,
                                                          groups__name__icontains=group,
                                                          usertests__test_name__name__icontains=test).exclude(
                        username='roman').distinct().order_by('last_name')
                else:
                    total_user_list = User.objects.filter(profile__ac_type__icontains=ac_type, profile__position__icontains=position,
                                                          groups__name__icontains=group).exclude(
                        username='roman').distinct().order_by('last_name')
                if not total_user_list:
                    no_search_result = True
                    results = f'Пилоты по запросу не найдены'
                    context = {'no_search_results': no_search_result, 'results': results,
                               'position_list': position_list, 'group_list': group_list, 'tests_list': test_list, 'ac_types': ac_types_list}
                    return render(request, 'user_list.html', context=context)
                else:
                    total_user_number = len(total_user_list)
                    paginator = Paginator(total_user_list, 20)
                    page_number = request.GET.get('page', 1)
                    users = paginator.page(page_number)
                    context = {'user_list': users, 'no_search_results': no_search_result,
                               'position_list': position_list, 'filter_input': filter_input,
                               'group_list': group_list, 'tests_list': test_list, 'user_test_dict': user_test_dict,
                               'user_num': total_user_number, 'ac_types': ac_types_list}
                    return render(request, 'user_list.html', context=context)

        else:
            total_user_list = User.objects.all().order_by('last_name').exclude(
                username='roman')  # Вынимаем всех пользователей, кроме superuser
            total_user_number = User.objects.all().exclude(username='roman').count()
            #  Постраничная разбивка
            paginator = Paginator(total_user_list, 20)
            page_number = request.GET.get('page', 1)
            users = paginator.page(page_number)
            context = {'user_list': users, 'no_search_results': no_search_result, 'position_list': position_list,
                       'group_list': group_list, 'tests_list': test_list, 'user_test_dict': user_test_dict,
                       'user_num': total_user_number, 'ac_types': ac_types_list}
            return render(request, 'user_list.html', context=context)


# Список пользователей конуретной группы
@login_required
@group_required('KRS')
def group_users(request, id):
    groups = Group.objects.all().values()
    group_list = []
    for group in groups:
        group_list.append(group)
    group_list.append({'name': 'Все'})  # Добавляем выбор всех групп
    position_list = Profile.Position.values
    position_list.append('Все')  # Добавляем вариант выбора всехдолжностей
    no_search_result = False
    total_user_list = User.objects.filter(groups=id).order_by('last_name')
    if not total_user_list:
        no_search_result = True
        group_name = Group.objects.get(id=id)  # .values('name')
        results = f'Пилоты в группе "{group_name.name}" не найдены'
        context = {'no_search_results': no_search_result, 'results': results,
                   'position_list': position_list, 'group_list': group_list}
        return render(request, 'user_list.html', context=context)
    paginator = Paginator(total_user_list, 20)
    page_number = request.GET.get('page', 1)
    users = paginator.page(page_number)
    context = {'user_list': users, 'no_search_results': no_search_result, 'position_list': position_list,
               'group_list': group_list}
    return render(request, 'user_list.html', context=context)


@login_required
@group_required('KRS')
def group_list(request, id=None):
    if request.method == 'POST':
        pass
    if id:
        pass
    else:
        groups = Group.objects.all()
        fixed_groups = common.fixed_groups
        print('fixed_groups:', fixed_groups)
        paginator = Paginator(groups, 20)
        page_number = request.GET.get('page', 1)
        groups_pages = paginator.page(page_number)
        context = {'groups': groups_pages, 'fixed_groups': fixed_groups}
        return render(request, 'group_list.html', context=context)


# Обрабатываем вызов деталей конкретной группы для назначения тестов
@login_required
@group_required('KRS')
def group_details(request, id):
    UserTestForm = formset_factory(TestsForUser, extra=0, formset=BaseUserTestFormSet,
                                   can_delete=True)  # Extra - количество строк формы
    group = Group.objects.get(id=id)
    if request.method == 'POST':
        tests_for_group_form = UserTestForm(request.POST, request.FILES)
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
                    print('total_user_list', total_user_list)
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
        print('tests_for_group_form', tests_for_group_form)
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
    Group.objects.get(id=id).delete()
    return redirect('quize737:group_list')


@login_required
@group_required('KRS')
def edit_user(request, id):
    position_list = Profile.Position.labels  # Вырианты выбора должности пилота
    ac_type_list = Profile.ACType.labels  # Варианты выбора типа ВС пилота
    user_obj = User.objects.get(id=id)  # Объект пользователя
    all_groups = Group.objects.all()  # Все существующие группы
    if request.method == 'POST':
        form_user = EditUserForm(request.POST, instance=user_obj)
        new_position = request.POST.get('position')  # Новая должность
        changed_groups = request.POST.getlist('group')  # Новые группы
        new_ac_type = request.POST.get('ac_type')  # Новый тип ВС
        old_position = user_obj.profile.position  #  Текущая (старая) должность
        old_ac_type = user_obj.profile.ac_type  #  Текущий (старый) тип ВС

        # Проверяем должность (квалификацию), при необходимости обновляем должность и группу
        for j in Profile.Position.choices:  # Выясняем соответсвие названию выбора и самому выбору
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
        for j in Profile.ACType.choices:  # Выясняем соответсвие названию выбора и самому выбору
            if j[1] == new_ac_type:
                new_ac_type = j[0]
                break
        if old_ac_type != new_ac_type:
            user_obj.profile.ac_type = new_ac_type
            user_obj.profile.save()

        #TODO: долелать автоматическое изменение группы, в случаем изменения типа ВС

        # Проверяем форму Логина и Email
        if form_user.is_valid():
            form_user.save()
            return redirect('quize737:user_list')
        else:
            form_user = EditUserForm(request.POST, instance=user_obj)
            form_profile = ProfileForm()
            context = {'user_obj': user_obj, 'all_groups': all_groups, 'position_list': position_list,
                       'form_user': form_user, 'form_profile': form_profile, 'ac_type': ac_type_list}
            return render(request, 'edit_user.html', context=context)
    else:
        form_user = EditUserForm(initial={"username": user_obj.username, 'email': user_obj.email})
        form_profile = ProfileForm()
        context = {'user_obj': user_obj, 'all_groups': all_groups, 'position_list': position_list,
                   'form_user': form_user, 'form_profile': form_profile, 'ac_type': ac_type_list}
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
        print("post:", request.POST)
        tests_for_user_form = UserTestForm(request.POST, request.FILES)
        if tests_for_user_form.is_valid():
            for test in tests_for_user_form.cleaned_data:
                #  Удаляем все объекты
                if test['DELETE']:
                    UserTests.objects.filter(user=user_object, test_name=test['test_name']).delete()
                else:
                    try:
                        if UserTests.objects.get(user=user_object, test_name=test['test_name']):
                            instance = UserTests.objects.get(user=user_object, test_name=test['test_name'])
                            instance.num_try = test['num_try']
                            instance.date_before = test['date_before']
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
            user_tests = UserTests.objects.filter(user=id).values('test_name', 'num_try', 'date_before')
            tests_for_user_form = UserTestForm(initial=user_tests)
            context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form, 'test_and_data_saved': True,
                       'user_id': id}
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

        # user_groups = user_obj.groups.all()
        # print('user_groups', user_groups)
        context = {'user_profile': user_profile[0], 'user_tests': tests_for_user_form, 'user_id': id}
        return render(request, 'user_ditales.html', context=context)


@login_required
@group_required('KRS')
def new_user(request):
    form_user = UserRegisterForm()
    form_profile = ProfileForm()
    if request.method == 'POST':
        form_user = UserRegisterForm(request.POST)
        form_profile = ProfileForm(request.POST)
        if form_user.is_valid() and form_profile.is_valid():
            group = Group.objects.get(name=form_profile.cleaned_data[
                                               'position'] + ' ' + form_profile.cleaned_data['ac_type'])  #- раскоментить и убрать 'B737'
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
                ac_type=form_profile.cleaned_data['ac_type'] # - Раскоментить на странице new_user.html возможность выбора типа ВС и в forms раскоментить поле ac_type
            )
            return redirect('quize737:user_list')

        else:
            context = {'form_user': form_user, 'form_profile': form_profile}
            return render(request, 'new_user.html', context=context)
    else:
        context = {'form_profile': form_profile, 'form_user': form_user}
        return render(request, 'new_user.html', context=context)


@login_required
@group_required('KRS')
def del_user(request, id):
    User.objects.get(id=id).delete()
    return redirect('quize737:user_list')


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
                print('filename', filename)
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
                            print('ERROR', error)
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
                                            if data:
                                                if re.search('[a-zA-Z]', str(data)):
                                                    print('this data!:::', data)
                                                    alpha = True
                                                    break
                                                elif re.search('[0-9]', str(data)):
                                                    # print('this data!:::', data)
                                                    alpha = True
                                                    break

                                    if alpha == True:
                                        wrong_data.append(f'Не заполненные поля в строке {reader.line_num}')
                                        # print("HEREEEEEE_2")
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
def issue_mess(request):
    q_id = int(request.POST.get('issue_q_id'))
    site_url = config('SITE_URL', default='')
    q_instance = QuestionSet.objects.get(id=q_id)
    emails = User.objects.filter(groups__name='Редактор').values('email')
    to = []  # Список email адресов для рассылки
    for email in emails:
        to.append(email['email'])
    subject = f'Ошибка в Вопросе'
    message = f'<p style="font-size: 20px;"><b>{request.user.profile.family_name} {request.user.profile.first_name} {request.user.profile.middle_name}</b></p><br>' \
              f'<p style="font-size: 15px;"><b>Сообщил об ошибке в вопросе:</b></p>' \
              f'<p style="font-size: 15px;"><b>{q_instance.question}</b></p>' \
              f'<a href="{site_url}/question_list/{q_id}">Редактировать вопрос</a>'
    email_msg = {'subject': subject, 'message': message, 'to': to}
    common.send_email(request, email_msg)

    return HttpResponse(request.POST)
