from django.db import models
from datetime import datetime
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
import pytz
from django.utils.timezone import now


# Модель тем вопросов
class Thems(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название Темы")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}'  # , id: {self.id}'


# Вся база вопросов по всем темам
class QuestionSet(models.Model):

    class ACType(models.TextChoices):
        B737 = 'B737', 'Boeing 737'
        B777 = 'B777', 'Boeing 777'
        A32X = 'A32X', 'Airbus 32X'
        A33X = 'A33X', 'Airbus 33X'
        ANY = 'ANY', 'ANY TYPE'

    # Имя темы связано с классом Them
    them_name = models.ForeignKey(Thems, on_delete=models.CASCADE, max_length=500, verbose_name='Тема Вопроса')
    question = models.TextField(verbose_name='Вопрос')
    option_1 = models.TextField(verbose_name='Вариант 1')
    option_2 = models.TextField(verbose_name='Вариант 2')
    option_3 = models.TextField(verbose_name='Вариант 3', blank=True, null=True)
    option_4 = models.TextField(verbose_name='Вариант 4', blank=True, null=True)
    option_5 = models.TextField(verbose_name='Вариант 5', blank=True, null=True)
    option_6 = models.TextField(verbose_name='Вариант 6', blank=True, null=True)
    option_7 = models.TextField(verbose_name='Вариант 7', blank=True, null=True)
    option_8 = models.TextField(verbose_name='Вариант 8', blank=True, null=True)
    option_9 = models.TextField(verbose_name='Вариант 9', blank=True, null=True)
    option_10 = models.TextField(verbose_name='Вариант 10', blank=True, null=True)
    q_kind = models.BooleanField(verbose_name='Несколько правильных ответов', default=False,
                                 help_text='Если вопрос подразумевает несколько правильных ответов')
    q_weight = models.FloatField(verbose_name='"Вес вопроса"', default=0.0,
                                 help_text='Если вопрос сложный или лёгкий, кол-во баллов за вопрос можно увеличить или уменьшить')
    answer = models.IntegerField(verbose_name='Ответ, в виде номера строки ответа',
                                 help_text='Поле используется если вопрос подразумевает один ответ, True - если один ответ, False - если несколько ответов',
                                 blank=True,
                                 null=True)
    answers = models.CharField(max_length=500, verbose_name='Ответы на вопрос',
                               help_text='Поле используется если вопрос подразумевает несколько правильных ответов',
                               blank=True, null=True)
    ac_type = models.CharField(max_length=10, verbose_name='Тип ВС', choices=ACType.choices, null=True)

    class Meta:
        ordering = ['-them_name']
        # indexes = [models.Index(fields=['question'])]

    def __str__(self):
        return f'{self.them_name}, {self.question}'


# Сгенерированнный Тест для конекретного пользователя, удаляется после завершения теста
class QuizeSet(models.Model):
    """Варианты тестов"""
    test_id = models.IntegerField(verbose_name='id теста из которого сформирован QuizeSet', null=True)
    quize_name = models.CharField(max_length=200, verbose_name='Название теста',
                                  help_text='Имя Теста + кол-во вопросов (без пробелов)')
    user_under_test = models.CharField(max_length=255, verbose_name='Имя пользователя',
                                       help_text='Имя пользователя, который проходит тест')
    timestamp = models.DateTimeField(verbose_name='Время и дата теста', default=now)  #datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M:%S')
    questions_ids = models.TextField(verbose_name='Номера вопросов', null=True,
                                     help_text='Сквозные Номера вопросов в базе данных вопросов, сгенерированные пользователю')
    q_sequence_num = models.IntegerField(default=0,
                                         verbose_name='Номер последовательного вопроса в тесте в процессе прохождения теста')
    max_score_amount = models.FloatField(verbose_name='Максимальное кол-во баллов',
                                         help_text='Максимально возможное количество баллов, если в вопроса был указан вес')
    pass_score = models.IntegerField(default=0, verbose_name='Количество правильных ответов',
                                     help_text='Минимальный процент правильных ответов для прохождения теста')

    def __str__(self):
        return self.quize_name


# Объект результат теста конкретного пользователя
class QuizeResults(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT, verbose_name='ID пользователя',
                                help_text='ID пользователя, для упрощённого поиска результатов', null=True,
                                default='User Deleted')
    user_name = models.CharField(max_length=255, verbose_name='Имя пользователя',
                                 help_text='Имя пользователя, который проходил тест')
    quize_name = models.CharField(max_length=200, verbose_name='Название теста',
                                  help_text='Имя Теста + кол-во вопросов (без пробелов)')
    total_num_q = models.IntegerField(verbose_name='Количество вопросов', help_text='Общее количество вопросов в тесте')
    timestamp = models.DateTimeField(verbose_name='Время и дата теста', default=now)
    questions_ids = models.TextField(verbose_name='Номера вопросов', null=True)
    correct_q_num = models.IntegerField(verbose_name='Количество правильных ответов')
    score_number = models.FloatField(verbose_name='Количество баллов')
    total_result = models.IntegerField(verbose_name='Общая оценка', null=True)
    pass_score = models.IntegerField(default=0, verbose_name='Количество правильных ответов',
                                     help_text='Минимальный процент правильных ответов для прохождения теста')
    conclusion = models.BooleanField(verbose_name='Итоговый результат', null=True,
                                     help_text='Итоговый результат, True - пользоваетль сдал тест или False - если пользоваетль тест не сдал')
    in_progress = models.BooleanField(verbose_name='Тест не завершён', default=True,
                                     help_text='Если тест не завершён, то результат не показывается в общем списке')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user_name} {self.timestamp.strftime("%d.%m.%Y %H:%M:%S")}'


#  Модель конструктора тестов - названия и id тестов
class TestConstructor(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название Теста',
                            help_text='Название теста которое будет видно пользователю')
    pass_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=80,
                                     verbose_name='Количество правильных ответов',
                                     help_text='Минимальный процент правильных ответов для прохождения теста')
    training = models.BooleanField(verbose_name='Тренировочный тест', default=False)

    ac_type = models.CharField(max_length=255, verbose_name='Тип ВС')

    email_to_send = models.TextField(verbose_name='email адреса для рассылки результатов', null=True)

    def __str__(self):
        return f'{self.name}'


# Модель конструктора тестов - сами вопросы для теста, записываются в отдельную таблицу
class TestQuestionsBay(models.Model):
    theme = models.ForeignKey(Thems, on_delete=models.CASCADE, max_length=500, verbose_name='Тема',
                              help_text='Тема из которой выбираются вопросы')
    test_id = models.ForeignKey(TestConstructor, on_delete=models.CASCADE, verbose_name='id теста',
                                help_text='id теста которому принадлежит вопрос')
    q_num = models.IntegerField(verbose_name='Количество вопросов по теме')

    # max_q_num = models.IntegerField(verbose_name='Максимальное Количество вопросов по теме', null=True)

    class Meta:
        unique_together = ('theme', 'test_id')

    def __str__(self):
        return f'{self.theme}, Test_id: {self.test_id}, вопросов: {self.q_num}'


class FileUpload(models.Model):
    docfile = models.FileField(upload_to='documents/')


#  Результаты ответов конкретного пользователя
class AnswersResults(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, max_length=500, verbose_name='Пользователь',
                             help_text='Объект пользователя', default='User Deleted')
    results = models.ForeignKey(QuizeResults, on_delete=models.CASCADE, max_length=500, verbose_name='Результаты теста',
                                help_text='Объект с результатами теста конкретного пользователя')
    question = models.ForeignKey(QuestionSet, on_delete=models.CASCADE, max_length=500, verbose_name='Результаты теста',
                                 help_text='Объект с результатами теста конкретного пользователя', default='Question Deleted')
    user_answer = models.CharField(max_length=255, verbose_name='Ответ пользователя',
                                   help_text='Ответ пользователя на вопрос')
    conclusion = models.BooleanField(verbose_name='Результат ответа', null=True,
                                     help_text='Результат ответа пользователя на вопрос')

    class Meta:
        unique_together = ('results', 'question')