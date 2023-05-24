from .models import QuestionSet, TestConstructor, TestQuestionsBay, Thems
from django import forms
from django.core.exceptions import ValidationError


# Валидатор для формы QuestionSetForm - проверят уникальность вопроса
def similar_question(value):
    questions = QuestionSet.objects.filter(question=value)
    if len(questions) > 0:
        raise ValidationError('Такой вопрос уже есть в базе')


# Класс для объектов редактирования и создания вопроса
class NewQuestionSetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewQuestionSetForm, self).__init__(*args, **kwargs)
        self.fields['question'].validators = [similar_question]

    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'q_kind',
                  'q_weight', 'answer', 'answers']


# Класс для объектов редактирования и создания вопроса
class QuestionSetForm(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'q_kind',
                  'q_weight', 'answer', 'answers']
        # widgets = {
        #     'question': forms.Textarea(attrs={'cols': 20, 'rows': 10})
        # }


# Валидатор для формы NewTestFormName - проверят уникальность имени теста
def similar_test_name(value):
    test_name = TestConstructor.objects.filter(name=value)
    if len(test_name) > 0:
        raise ValidationError('Тест с таким именем уже существует')

# Форма для имени создаваемого и теста
class NewTestFormName(forms.Form):

    def __init__(self, *args, **kwargs):
        super(NewTestFormName, self).__init__(*args, **kwargs)
        self.fields['name'].validators = [similar_test_name]

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
        # help_text='max. 42 megabytes'
    )


# Валидатор для формы NewThemeForm - проверят уникальность темы
def similar_name_check(value):
    themes_names = Thems.objects.filter(name=value)
    print('names:', themes_names)
    if len(themes_names) > 0:
        raise ValidationError('Тема с таким именем уже существует')


# Форма создания новой темы
class NewThemeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewThemeForm, self).__init__(*args, **kwargs)
        self.fields['name'].validators = [similar_name_check]

    class Meta:
        model = Thems
        fields = ['name']
