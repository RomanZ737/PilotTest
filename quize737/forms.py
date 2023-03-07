from .models import QuestionSet
from django import forms


# Класс для объектов редактирования вопроса
class QuestionSetForm(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'q_kind', 'q_weight', 'answer', 'answers']
