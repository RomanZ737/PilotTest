from .models import QuestionSet, TestConstructor, TestQuestionsBay, Thems
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Textarea, NumberInput


# Валидатор для формы QuestionSetForm - проверят уникальность вопроса
def similar_question(value):
    questions = QuestionSet.objects.filter(question=value)
    if len(questions) > 0:
        raise ValidationError('Такой вопрос уже есть в базе')


# Класс для объектов создания вопроса
class NewQuestionSetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewQuestionSetForm, self).__init__(*args, **kwargs)
        self.fields['question'].validators = [similar_question]  # Добавляем валидатор одинаковых вопросв к форме
        self.fields['them_name'].queryset = Thems.objects.all().exclude(
            name='Все темы')  # Исключаем 'Все темы' из опции выбора

    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'option_6',
                  'option_7', 'option_8', 'option_9', 'option_10', 'q_kind',
                  'q_weight', 'answer', 'answers', 'ac_type']

        widgets = {
            'q_weight': forms.NumberInput(attrs={'size': '3', 'step': 0.5, 'max': 2.0, 'min': 0.0}),
            'question': forms.Textarea(attrs={'cols': 150, 'rows': 1}),
            'option_1': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_2': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_3': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_4': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_5': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_6': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_7': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_8': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_9': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_10': forms.Textarea(attrs={'cols': 100, 'rows': 1})
        }


# Класс для объектов редактирования вопроса
class QuestionSetForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionSetForm, self).__init__(*args, **kwargs)
        self.fields['them_name'].queryset = Thems.objects.all().exclude(
            name='Все темы')  # Исключаем 'Все темы' из опции выбора

    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'option_6',
                  'option_7', 'option_8', 'option_9', 'option_10', 'q_kind',
                  'q_weight', 'answer', 'answers', 'ac_type']
        widgets = {
            'q_weight': forms.NumberInput(attrs={'size': '3', 'step': 0.5, 'max': 2.0, 'min': 0.0})
        }


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
    pass_score = forms.IntegerField(initial=80, widget=forms.NumberInput(attrs={'size': '4',
                                                                                'max': '100',  # For maximum number
                                                                                'min': '0',  # For minimum number
                                                                                }))
    training = forms.BooleanField(initial=False, required=False)


# Форма для вопросов создаваемого теста
class NewTestFormQuestions(forms.ModelForm):

    theme = forms.ChoiceField()

    class Meta:
        model = TestQuestionsBay
        fields = ['q_num']
        error_messages = {'q_num': {'required': "Поле количества вопросов не может быть пустым"}}
        widgets = {
            "q_num": NumberInput(attrs={'size': '6', 'min': '1'}),
        }


# https://docs.djangoproject.com/en/2.2/topics/forms/formsets/#passing-custom-parameters-to-formset-forms
# Форма, которая принимает кастомный аргумент со списком полей выбора. Наследуется от формы NewTestFormQuestions. Используемтся для Form Factory
class MyNewTestFormQuestions(NewTestFormQuestions):
    def __init__(self, *args, thems_selection, **kwargs):
        self.thems_selection = thems_selection
        super(MyNewTestFormQuestions, self).__init__(*args, **kwargs)
        self.fields['theme'].choices = self.thems_selection


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


#  форма сообщения администратору (в модальном окне)
class AdminMessForm(forms.Form):
    subject = forms.CharField(widget=forms.Textarea(attrs={'rows': 1, 'style': 'font-size: 18'}), help_text="Тема сообщения")
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 7, 'style': 'font-size: 18'}))
