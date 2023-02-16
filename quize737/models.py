from django.db import models
from django.utils.timezone import now


class Thems(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название Темы")

    def __str__(self):
        return self.name


# Вся база вопросов по всем темам
class QuestionSet(models.Model):
    # Имя темы связано с классом Nhem

    them_name = models.ForeignKey(Thems, on_delete=models.CASCADE, max_length=500, verbose_name='Тема Вопроса')
    question = models.CharField(max_length=500, verbose_name='Вопрос')
    option_1 = models.CharField(max_length=500, verbose_name='Вариант 1')
    option_2 = models.CharField(max_length=500, verbose_name='Вариант 2')
    option_3 = models.CharField(max_length=500, verbose_name='Вариант 3', blank=True, null=True)
    option_4 = models.CharField(max_length=500, verbose_name='Вариант 4', blank=True, null=True)
    q_kind = models.BooleanField(verbose_name='Вид вопроса', default=False,
                                 help_text='Подразумевает ли вопрос множественные ответы')
    q_weight = models.IntegerField(verbose_name='"Вес вопроса"', default=0,
                                   help_text='Если вопрос сложный или лёгкий, кол-во баллов за вопрос можно увеличить или уменьшить')
    answer = models.IntegerField(verbose_name='Ответ, в виде номера строки ответа')

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
    timestamp = models.DateTimeField(default=now)
    questions_ids = models.CharField(max_length=200, verbose_name='Номера вопросов', null=True, help_text='Сквозные Номера вопросов сгенерированные пользователю')
    q_sequence_num = models.IntegerField(default=0,
                                         verbose_name='Номер последовательного вопроса в тесте в процессе прохождения теста')

    def __str__(self):
        return self.quize_name


# Объект результат теста конкретного пользователя
class QuizeResults(models.Model):
    user_name = models.CharField(max_length=255, verbose_name='Имя пользователя',
                                 help_text='Имя пользователя, который проходил тест')
    quize_name = models.CharField(max_length=200, verbose_name='Название теста',
                                  help_text='Имя Теста + кол-во вопросов (без пробелов)')
    total_num_q = models.IntegerField(verbose_name='Количество вопросов', help_text='Общее количество вопросов в тесте')
    timestamp = models.DateTimeField(default=now)
    questions_ids = models.CharField(max_length=200, verbose_name='Номера вопросов', null=True)
    correct_q_num = models.IntegerField(verbose_name='Количество правильных ответов')
    score_number = models.IntegerField(verbose_name='Количество баллов')

    def __str__(self):
        return f'{self.user_name} {self.timestamp}'
