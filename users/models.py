from django.db import models
from django.contrib.auth.models import User, Group
from quize737.models import TestConstructor
import datetime
from field_validators.validators import validate_not_zero


class Profile(models.Model):
    class Position(models.TextChoices):
        PIC = 'КВС', 'Командир ВС'
        COPILOT = 'ВП', 'Второй пилот'
        INSTRUCTOR = 'ПИ', 'Пилот-инструктор'

    class ACType(models.TextChoices):
        B737 = 'B737', 'ВС Boeing 737'
        B777 = 'B777', 'ВС Boeing 777'
        A32X = 'A32X', 'ВС Airbus 32X'
        A33X = 'A33X', 'ВС Airbus 33X'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    family_name = models.CharField(max_length=30, verbose_name='Фамилия', default=None)
    first_name = models.CharField(max_length=30, verbose_name='Имя', default=None)
    middle_name = models.CharField(max_length=30, verbose_name='Отчество', default=None)
    position = models.CharField(max_length=10, verbose_name='Должность', choices=Position.choices)
    ac_type = models.CharField(max_length=10, verbose_name='Тип ВС', choices=ACType.choices)

    def position_readable(self):
        # Get value from choices enum
        return self.Position[self.position]

    class Meta:
        ordering = ['family_name']
        indexes = [models.Index(fields=['family_name', 'first_name'])]

    # def __str__(self):
    #     return f'{self.family_name} {self.first_name}'

    def __str__(self):
        return "{id}, {profile_id}, {family_name} {first_name} {value} ({display_value})".format(  profile_id=self.id,
                                                                                    id=self.user.id,
                                                                                    family_name=self.family_name,
                                                                                    first_name=self.first_name,
                                                                                    value=self.position,
                                                                                    display_value=self.get_position_display())


#  Модель для описания группы
class GroupsDescription(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    discription = models.CharField(max_length=200, verbose_name='Описание Группы', default=None)

    def __str__(self):
        return f'{self.group}'


# Модель теста, назначенного пользователю
class UserTests(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_name = models.ForeignKey(TestConstructor, on_delete=models.CASCADE)
    num_try_initial = models.IntegerField(verbose_name='Изначальное Количество попыток', null=True)
    num_try = models.IntegerField(default=3, validators=[validate_not_zero], verbose_name='Количество попыток')
    date_before = models.DateTimeField(default=(datetime.datetime.now() + datetime.timedelta(days=30)).date(),
                                       verbose_name='Дата до которой необходимо выполнить тест')

    class Meta:
        unique_together = ('user', 'test_name')

    def __str__(self):
        return f'Пилот {self.user.last_name} {self.user.first_name}, --> {self.test_name}, попыток {self.num_try}, закончить до {self.date_before.strftime("%d.%m.%Y %H:%M")}'


#  Модель просроченных тестов пользователя
class TestExpired(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Модель пользователя')
    test = models.ForeignKey(UserTests, on_delete=models.CASCADE, verbose_name='Модель теста пользователя')
    days_left = models.IntegerField(verbose_name='Количество дней до истечения', null=True)

    class Meta:
        unique_together = ('user', 'test')

    def __str__(self):
        return f'{self.user.last_name} {self.user.first_name}, Test: {self.test.test_name}, Дата: {self.test.date_before.strftime("%d.%m.%Y %H:%M")}'
