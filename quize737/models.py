from django.db import models


class QuestionSet(models.Model):
    # Задаём имена систем
    them_names = [('Electrical', 'Electrical'), ('Engine', 'Engine'), ('Landin Gear', 'Landin Gear')]

    them_name = models.CharField(max_length=500, verbose_name='Тема Вопроса', choices=them_names)
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


class QuizeSet(models.Model):
    """Варианты тестов стандарнтых тестов"""
    quize_name = models.CharField(max_length=255, verbose_name='Название Теста')

    def __str__(self):
        return self.quize_name


