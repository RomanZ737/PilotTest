from django.db import models
from django.utils.timezone import now

class Thems(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название Темы")

    def __str__(self):
        return self.name

# Вся база вопросов по всем темама
class QuestionSet(models.Model):

    # Имя темы связано с классом Nhem

    them_name = models.ForeignKey(Thems, on_delete=models.CASCADE, max_length=500, verbose_name='Тема Вопроса')
    question = models.CharField(max_length=500, verbose_name='Вопрос')
    option_1 = models.CharField(max_length=500, verbose_name='Вариант 1')
    option_2 = models.CharField(max_length=500, verbose_name='Вариант 2')
    option_3 = models.CharField(max_length=500, verbose_name='Вариант 3', blank=True, null=True)
    option_4 = models.CharField(max_length=500, verbose_name='Вариант 4', blank=True, null=True)
    answer = models.IntegerField(verbose_name='Ответ, в виде номера строки ответа')

    class Meta:
        ordering = ['-them_name']

    def __str__(self):
        return f'{self.them_name}, {self.question}'

# Сгенерированнный Тест для конекретного пользователя
class QuizeSet(models.Model):

    """Варианты тестов"""
    quize_name = models.CharField(max_length=200, verbose_name='Название теста', help_text='Вид Теста + кол-во вопросов')
    user_under_test = models.CharField(max_length=255, verbose_name='Имя пользователя')
    timestamp = models.DateTimeField(default=now)
    questions_ids = models.CharField(max_length=200, verbose_name='Номера вопросов', null=True)
    q_sequence_num = models.IntegerField(default=0, verbose_name='Номер последовательного вопроса в тесте в процессе прохождения теста')

    def __str__(self):
        return self.quize_name

