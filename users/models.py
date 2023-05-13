from django.db import models
from django.contrib.auth.models import User
from quize737.models import TestConstructor
import datetime

class Profile(models.Model):
    class Position(models.TextChoices):
        PIC = 'КВС', 'Командир ВС'
        COPILOT = 'ВП', 'Второй пилот'
        INSTRUCTOR = 'ПИ', 'Пилот-инструктор'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    family_name = models.CharField(max_length=500, verbose_name='Фамилия', default=None)
    first_name = models.CharField(max_length=500, verbose_name='Имя', default=None)
    middle_name = models.CharField(max_length=500, verbose_name='Отчество', default=None)
    position = models.CharField(max_length=10, verbose_name='Должность', choices=Position.choices)

    def position_readable(self):
        # Get value from choices enum
        return self.Position[self.position]

    class Meta:
        ordering = ['family_name']

    # def __str__(self):
    #     return f'{self.family_name} {self.first_name}'

    def __str__(self):
        return "{value} ({display_value})".format(value=self.position, display_value=self.get_position_display())


# Модель теста, назначенного пользователю
class UserTests(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_name = models.ForeignKey(TestConstructor, on_delete=models.CASCADE)
    num_try = models.IntegerField(default=3, verbose_name='Количество попыток')
    date_before = models.DateTimeField(default=(
                datetime.datetime.now() + datetime.timedelta(days=30)), verbose_name='Дата до которой необходимо выполнить тест')

    class Meta:
        unique_together = ('user', 'test_name')

    def __str__(self):
        return f'Пилот {self.user.last_name} {self.user.first_name}, --> {self.test_name}, попыток {self.num_try}, закончить до {self.date_before.strftime("%d.%m.%Y %H:%M")}'

