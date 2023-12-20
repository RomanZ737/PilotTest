from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User


class UserChangeLog(models.Model):
    user_changed = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ID пользователя',
                                     help_text='Объект пользователя который подвергся изменениям')
    timestamp = models.DateTimeField(verbose_name='Время и дата события', default=now)
    description = models.TextField(verbose_name='Описание изменения')
    test_name = models.CharField(max_length=500, verbose_name='Название теста',
                                 help_text='Название теста, если он учавствует в событии',
                                 blank=True, null=True)
    test_date_due = models.DateTimeField(verbose_name='Время и дата события', null=True,
                                         help_text='Дата до которой надо выполнить тест',)
    user_done = models.TextField(verbose_name='Описание изменения',
                                 help_text='ФИО пользователя который сделал изменения')

    class Meta:
        ordering = ['-timestamp']
        # indexes = [models.Index(fields=['question'])]

    def __str__(self):
        return f'{self.timestamp.strftime("%d.%m.%Y %H:%M:%S")}, ' \
               f'{self.user_changed}, {self.description}'