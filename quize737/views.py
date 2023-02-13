from django.shortcuts import render
from .models import QuestionSet, QuizeSet


def index(request):
    """Отображение домашней страницы"""

    # Генерируем список доступных тестов
    all_quiz = QuizeSet.objects.all().values()

    # Отрисовка HTML-страницы с данными внутри в переменой context
    return render(request,
                  'index.html',
                  context={'all_quiz': all_quiz}
                  )


def question(request):
    selected_questons = [x for x in QuestionSet.objects.all()]
    context = {'selected_questons': selected_questons}

    return render(request, 'question.html', context=context)
