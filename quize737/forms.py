from .models import QuestionSet, TestConstructor, TestQuestionsBay, Thems
from django import forms


# Класс для объектов редактирования вопроса
class QuestionSetForm(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'q_kind',
                  'q_weight', 'answer', 'answers']


# Форма для имени создаваемого и теста
class NewTestFormName(forms.Form):
    test_name = forms.CharField(max_length=25, initial='Новый Тест')


# Форма для вопросов создаваемого теста
class NewTestFormQuestions(forms.Form):
    them = forms.ModelChoiceField(queryset=Thems.objects.all(), empty_label='Все темы', required=False)
    q_num = forms.IntegerField(label='Количество вопросов', error_messages={'required': 'Количество вопросов не может быть пустым'}, required=True)
