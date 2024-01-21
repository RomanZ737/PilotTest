from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from choices import LogDescription


# Объект логирования действий пользователя
class UserChangeLog(models.Model):
    user_changed = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ID пользователя',
                                     help_text='Объект пользователя который подвергся изменениям')
    timestamp = models.DateTimeField(verbose_name='Время и дата события', default=now)
    description = models.TextField(verbose_name='Описание изменения', choices=LogDescription.choices)
    test_id = models.CharField(max_length=500, verbose_name='ID теста',
                               help_text='ID теста, если он участвует в событии',
                               blank=True, null=True)
    test_name = models.CharField(max_length=500, verbose_name='Название теста',
                                 help_text='Название теста, если он участвует в событии',
                                 blank=True, null=True)
    test_date_due = models.DateTimeField(verbose_name='Время и дата теста', null=True,
                                         help_text='Дата до которой надо выполнить тест', )
    old_date = models.DateTimeField(verbose_name='Изначальные время и дата теста', null=True,
                                    help_text='Изначальные время и дата до которой надо выполнить тест', )
    new_date = models.DateTimeField(verbose_name='Новые время и дата теста', null=True,
                                    help_text='Новые время и дата до которой надо выполнить тест', )
    old_num_try = models.IntegerField(verbose_name='Изначальное ко-во попыток',
                                      help_text='Количество попыток, которое было у пользователя изначально',
                                      blank=True,
                                      null=True)
    new_num_try = models.IntegerField(verbose_name='Новое ко-во попыток',
                                      help_text='Количество попыток, которое было установлено пользователю',
                                      blank=True,
                                      null=True)
    user_done = models.TextField(verbose_name='Кто сделал изменение',
                                 help_text='ФИО пользователя который сделал изменения')

    class Meta:
        ordering = ['-timestamp']
        # indexes = [models.Index(fields=['question'])]

    def __str__(self):
        return f'{self.timestamp.strftime("%d.%m.%Y %H:%M:%S")}, ' \
               f'{self.user_changed}, {self.description}'
