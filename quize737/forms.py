from .models import QuestionSet, TestConstructor, TestQuestionsBay, Thems
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Textarea, NumberInput, ChoiceField, TextInput


# Валидатор для формы QuestionSetForm - проверят уникальность вопроса
def similar_question(value):
    questions = QuestionSet.objects.filter(question=value)
    if len(questions) > 0:
        raise ValidationError('Такой вопрос уже есть в базе')


class IMGform(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['question_img', 'comment_img']
        widgets = {'comment_text': forms.Textarea(attrs={'cols': 80, 'rows': 10})}
        error_messages = {'question_img': {'invalid_image': "Не верный формат файла"},
                          'comment_img': {'invalid_image': "Не верный формат файла"}}


# Класс для объектов создания вопроса
class NewQuestionSetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewQuestionSetForm, self).__init__(*args, **kwargs)
        self.fields['question'].validators = [similar_question]  # Добавляем валидатор одинаковых вопросв к форме
        self.fields['them_name'].queryset = Thems.objects.all().exclude(
            name='Все темы')  # Исключаем 'Все темы' из опции выбора

    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4',
                  'option_5', 'option_6', 'option_7', 'option_8', 'option_9', 'option_10',
                  'q_kind', 'q_weight', 'answer', 'answers', 'ac_type',
                  'is_for_center', 'is_timelimited', 'is_active', 'question_img', 'comment_img', 'comment_text']

        widgets = {
            'q_weight': forms.NumberInput(attrs={'size': '4', 'step': 0.5, 'max': 3.0, 'min': 0.0}),
            'question': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_1': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_2': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_3': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_4': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_5': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_6': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_7': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_8': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_9': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'option_10': forms.Textarea(attrs={'cols': 100, 'rows': 1}),
            'comment_text': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
            'answer': forms.NumberInput(attrs={'size': '4', 'step': 1, 'max': 10, 'min': 1}),
            'answers': forms.TextInput(attrs={"placeholder": "ex. 1,2,3,4..."})
        }


# Класс для объектов редактирования вопроса
class QuestionSetForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionSetForm, self).__init__(*args, **kwargs)
        self.fields['them_name'].queryset = Thems.objects.all().exclude(
            name='Все темы')  # Исключаем 'Все темы' из опции выбора

    class Meta:
        model = QuestionSet
        fields = ['them_name', 'question', 'option_1', 'option_2', 'option_3', 'option_4',
                  'option_5', 'option_6', 'option_7', 'option_8', 'option_9', 'option_10',
                  'q_kind', 'q_weight', 'answer', 'answers', 'ac_type', 'is_active',
                  'is_for_center', 'is_timelimited', 'question_img', 'comment_img', 'comment_text']
        widgets = {
            'q_weight': forms.NumberInput(attrs={'size': '4', 'step': 0.5, 'max': 3.0, 'min': 0.0}),
            'answer': forms.NumberInput(attrs={'size': '4', 'step': 1, 'max': 10, 'min': 1}),
            'comment_text': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
        }


# Валидатор для формы NewTestFormName - проверят уникальность имени теста
def similar_test_name(value):
    test_name = TestConstructor.objects.filter(name=value)
    if len(test_name) > 0:
        raise ValidationError('Тест с таким именем уже существует')


# Форма для имени и параметров создаваемого и теста
# class NewTestFormName(forms.Form):
#
#     def __init__(self, *args, **kwargs):
#         super(NewTestFormName, self).__init__(*args, **kwargs)
#         self.fields['name'].validators = [similar_test_name]
#
#     name = forms.CharField(max_length=25, initial='Новый Тест')
#     pass_score = forms.IntegerField(widget=forms.NumberInput(attrs={'size': '4',
#                                                                                 'max': '100',  # For maximum number
#                                                                                 'min': '0',  # For minimum number
#                                                                                 }))
#     training = forms.BooleanField(initial=False, required=False)

class NewTestFormName(forms.ModelForm):
    class Meta:
        model = TestConstructor
        fields = ['name', 'pass_score', 'set_mark', 'mark_four', 'mark_five', 'training',
                  'ac_type', 'email_to_send', 'is_active', 'comment', 'for_user_comment']
        widgets = {
            "pass_score": NumberInput(attrs={'size': '4', 'min': 0, 'max': 100}),
            "mark_four": NumberInput(attrs={'size': '4', 'max': 100}),
            "mark_five": NumberInput(attrs={'size': '4', 'max': 100}),
        }


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
        self.fields['theme'].widget = forms.Select(attrs={'class': 'select_them'})
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
    subject = forms.CharField(widget=forms.Textarea(attrs={'rows': 1, 'style': 'font-size: 18'}),
                              help_text="Тема сообщения")
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 7, 'style': 'font-size: 18'}))


#  форма сообщения об ошибке в вопросе (в модальном окне)
class QuestionIssueMess(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'style': 'font-size: 18',
                                                           'placeholder': 'Желательно, но не обязательно...'}),
                              required=False)
