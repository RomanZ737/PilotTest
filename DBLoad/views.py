from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from quize737.models import QuestionSet, QuizeResults


# Меняем Тип ВС в вопросах
@login_required
def alter_questions(request):
    them_list = ['АБ и СУБП', 'Законодательство', 'МЕТЕО', 'Навигация', 'Основы Полёта', 'Полёты в ОУ', 'Радиообмен']
    for them in them_list:
        q_set = QuestionSet.objects.filter(them_name__name=them)
        for q in q_set:
            q.ac_type = 'ANY'
            q.save()

    return redirect('quize737:start')

# Добавляем дату сдачи в результаты и количество попыток
@login_required
def alter_results(request):
    all_results = QuizeResults.objects.all()
    for result in all_results:
        result.date_end = result.timestamp
        if result.conclusion:
            result.try_spent = 1
        else:
            result.try_spent = 3
        result.total_num_try = 3
        result.save()
    return redirect('quize737:start')