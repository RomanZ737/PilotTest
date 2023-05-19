from .models import QuestionSet, TestConstructor, TestQuestionsBay, Thems
from django import forms


# Класс для объектов редактирования и создания вопроса
class QuestionSetForm(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'q_kind',
                  'q_weight', 'answer', 'answers']
        # widgets = {
        #     'question': forms.Textarea(attrs={'cols': 20, 'rows': 10})
        # }


# Форма для имени создаваемого и теста
class NewTestFormName(forms.Form):
    name = forms.CharField(max_length=25, initial='Новый Тест')
    pass_score = forms.IntegerField(initial=70, widget=forms.NumberInput(attrs={'size': '5',
                                                                                'max': '100',  # For maximum number
                                                                                'min': '0',  # For minimum number
                                                                                }))


# Форма для вопросов создаваемого теста
class NewTestFormQuestions(forms.ModelForm):
    class Meta:
        model = TestQuestionsBay
        fields = ['theme', 'q_num']

        # labels = {'name': _('Writer'),}
        # help_texts = {'name': _('Some useful help text.'),}
        error_messages = {'q_num': {'required': "Поле количества вопросов не может быть пустым"}, }


#  Форма для загрузки файла
class FileUploadForm(forms.Form):
    docfile = forms.FileField(
        label='Выберите файл',
        #help_text='max. 42 megabytes'
    )
