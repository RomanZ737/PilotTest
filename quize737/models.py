from django.db import models
from datetime import datetime


# Модель тем вопросов
class Thems(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название Темы")

    def __str__(self):
        return f'{self.name}'#, id: {self.id}'


# Вся база вопросов по всем темам
class QuestionSet(models.Model):
    # Имя темы связано с классом Nhem

    them_name = models.ForeignKey(Thems, on_delete=models.CASCADE, max_length=500, verbose_name='Тема Вопроса')
    question = models.CharField(max_length=500, verbose_name='Вопрос')
    option_1 = models.CharField(max_length=500, verbose_name='Вариант 1')
    option_2 = models.CharField(max_length=500, verbose_name='Вариант 2')
    option_3 = models.CharField(max_length=500, verbose_name='Вариант 3', blank=True, null=True)
    option_4 = models.CharField(max_length=500, verbose_name='Вариант 4', blank=True, null=True)
    option_5 = models.CharField(max_length=500, verbose_name='Вариант 5', blank=True, null=True)
    q_kind = models.BooleanField(verbose_name='Несколько правильных ответов', default=False,
                                 help_text='Если вопрос подразумевает несколько правильных ответов')
    q_weight = models.FloatField(verbose_name='"Вес вопроса"', default=0,
                                 help_text='Если вопрос сложный или лёгкий, кол-во баллов за вопрос можно увеличить или уменьшить')
    answer = models.IntegerField(verbose_name='Ответ, в виде номера строки ответа',
                                 help_text='Поле используется если вопрос подразумевает один ответ', blank=True,
                                 null=True)
    answers = models.CharField(max_length=500, verbose_name='Ответы на вопрос',
                               help_text='Поле используется если вопрос подразумевает несколько правильных ответов',
                               blank=True, null=True)

    class Meta:
        ordering = ['-them_name']

    def __str__(self):
        return f'{self.them_name}, {self.question}'


# Сгенерированнный Тест для конекретного пользователя
class QuizeSet(models.Model):
    """Варианты тестов"""
    quize_name = models.CharField(max_length=200, verbose_name='Название теста',
                                  help_text='Имя Теста + кол-во вопросов (без пробелов)')
    user_under_test = models.CharField(max_length=255, verbose_name='Имя пользователя',
                                       help_text='Имя пользователя, который проходит тест')
    timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    questions_ids = models.CharField(max_length=200, verbose_name='Номера вопросов', null=True,
                                     help_text='Сквозные Номера вопросов в базе данных вопросов, сгенерированные пользователю')
    q_sequence_num = models.IntegerField(default=0,
                                         verbose_name='Номер последовательного вопроса в тесте в процессе прохождения теста')
    max_score_amount = models.IntegerField(default=0, verbose_name='Максимальное кол-во баллов',
                                           help_text='Максимально возможное количество баллов, если в вопроса был указан вес')

    def __str__(self):
        return self.quize_name


# Объект результат теста конкретного пользователя
class QuizeResults(models.Model):
    user_name = models.CharField(max_length=255, verbose_name='Имя пользователя',
                                 help_text='Имя пользователя, который проходил тест')
    quize_name = models.CharField(max_length=200, verbose_name='Название теста',
                                  help_text='Имя Теста + кол-во вопросов (без пробелов)')
    total_num_q = models.IntegerField(verbose_name='Количество вопросов', help_text='Общее количество вопросов в тесте')
    timestamp = models.DateTimeField(verbose_name='Время и дата теста', default=datetime.now)
    questions_ids = models.CharField(max_length=200, verbose_name='Номера вопросов', null=True)
    correct_q_num = models.IntegerField(verbose_name='Количество правильных ответов')
    score_number = models.IntegerField(verbose_name='Количество баллов')
    total_result = models.IntegerField(verbose_name='Общая оценка', null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user_name} {self.timestamp.strftime("%d.%m.%Y %H:%M:%S")}'
    # .strftime("%d.%m.%Y %H:%m:%S")


#  Модель конструктора тестов - названия и id тестов
class TestConstructor(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название Теста',
                            help_text='Название теста которое будет видно пользователю')
    def __str__(self):
        return f'{self.name} {self.id}'


# Модель конструктора тестов - сами вопросы для теста
class TestQuestionsBay(models.Model):
    theme = models.ForeignKey(Thems, on_delete=models.CASCADE, max_length=500, verbose_name='Тема',
                              help_text='Тема из которой выбираются вопросы')
    test_id = models.ForeignKey(TestConstructor, on_delete=models.CASCADE, verbose_name='id теста',
                                help_text='id теста которому принадлежит вопрос')
    q_num = models.IntegerField(verbose_name='Количество вопросов по теме')

    class Meta:
        unique_together = ('theme', 'test_id')

    def __str__(self):
        return f'{self.theme}, Test_id: {self.test_id}, вопросов: {self.q_num}'
