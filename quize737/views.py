import random

from django.shortcuts import render
from .models import QuestionSet, QuizeSet, Thems, QuizeResults
from django.contrib.auth.decorators import login_required



# Заглавная страница
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

        #DEBUG PRINT
        # print(f'int(thems_num): {int(thems_num)} * int(request.POST.get("q_num")): {int(request.POST.get("q_num"))} = {int(thems_num) * int(request.POST.get("q_num"))}')

        total_q_num_for_user = int(thems_num) * int(request.POST.get("q_num"))

        user_quize_set = QuizeSet.objects.create(
            quize_name=str(request.POST.get("user_name") + "_All_Thems_For_" + request.POST.get("q_num")).replace(' ', '')+ 'q',
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
        user_set_name = str(request.POST.get('user_name') + "_All_Them_For_"+request.POST.get('q_num')).replace(' ', '') + 'q'

        # Выясняем количество сгенерированных вопросов
        q_amount = QuizeSet.objects.filter(id=user_quize_set.id).values('q_sequence_num')

        # Выясняем сквозные номера вопросов, сгенерированные пользователю
        q_num_list = QuizeSet.objects.filter(id=user_quize_set.id).values('questions_ids')

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
        QuizeSet.objects.filter(id=user_quize_set.id).update(q_sequence_num=sequence_number)

        # Создаём запись с результатами теста
        result_obj = QuizeResults.objects.create(
            user_name=request.POST.get('user_name'),
            quize_name=user_set_name,
            total_num_q=sequence_number+1,
            questions_ids=', '.join(q_num_list), #[str(x) for x in q_num_list],
            correct_q_num=0,
            score_number=0
        )

        #results_object_id = QuizeResults.objects.filter(user_name=request.POST.get('user_name')).values('id')
        context = {'user_name': request.POST.get("user_name"), 'question': question, 'user_set_id': user_quize_set.id, 'results_object_id': result_obj.id}

        return render(request, 'start_test.html', context=context)

    else:
        return render(request, 'start_all_q.html')

# Генерация последующих вопросов
def next_question(request):
    # Проверяем нажал ли пользователь кнопку "ответить"
    if request.method == 'POST':

        # Сравниваем результат ответа
        print('user_set_id: ', request.POST.get('user_set_id'))
        print('correct_answer: ', request.POST.get('answer'))
        print('user_answer:', request.POST.get('user_answer'))
        print('results_object_id:', request.POST.get('results_object_id'))
        print('q_weight: ', request.POST.get('q_weight'))

        # Если пользователь правильно ответил на вопрос:
        if request.POST.get('answer') == request.POST.get('user_answer'):

            # Вынимаем текущее количество правильных ответов и количество баллов пользователя
            user_result_data = QuizeResults.objects.filter(id=request.POST.get('results_object_id')).values('correct_q_num', 'score_number')

            # Увеличиваем количество правильных ответов на единицу и записыввем в базу
            QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(correct_q_num=(user_result_data[0]['correct_q_num'] + 1))


            # Увеличиваем колличество баллов пользователя, с учётов веса вопроса, если вес есть
            if int(request.POST.get('q_weight')) != 0:
                updated_score_number = user_result_data[0]['score_number'] + int(request.POST.get('q_weight'))

            else:
                updated_score_number = user_result_data[0]['score_number'] + 1

            # Обновляем количетво баллов
            QuizeResults.objects.filter(id=request.POST.get('results_object_id')).update(score_number=updated_score_number)

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
                       'question': question, 'results_object_id': request.POST.get('results_object_id')}

            # Обновляем количество оставшихся вопросов
            QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).update(q_sequence_num=question_sequence)

            return render(request, 'start_test.html', context=context)

        else:
            # Вынимаем количество правильных ответов, число вопросов и количество баллов
            result_data = QuizeResults.objects.filter(id=int(request.POST.get('results_object_id'))).values('correct_q_num', 'score_number', 'total_num_q')

            # Вынимаем количество максимально возможных баллов
            max_score_num = QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).values('max_score_amount')

            # Вычисляем процент прохождения теста и округляем результат до десятой
            total_result = ('%.1f' % ((result_data[0]['score_number'] * 100)/max_score_num[0]['max_score_amount']))

            # Формируем данные для отправки
            context = {'user_name': request.POST.get("user_name"), 'total_num_q': result_data[0]['total_num_q'], 'correct_q_num': result_data[0]['correct_q_num'], 'total_result': total_result}

            # Удаляем тест пользователя их базы
            QuizeSet.objects.filter(id=int(request.POST.get('user_set_id'))).delete()

            return render(request, 'results.html', context=context)




