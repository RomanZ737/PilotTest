from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from quize737.models import QuestionSet


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