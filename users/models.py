from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    family_name = models.CharField(max_length=500, verbose_name='Фамилия', default=None)
    first_name = models.CharField(max_length=500, verbose_name='Имя', default=None)
    middle_name = models.CharField(max_length=500, verbose_name='Отчество', default=None)
    position = models.CharField(max_length=500, verbose_name='Должность', default=None)

    def __str__(self):
        return f'{self.family_name} {self.first_name}'
