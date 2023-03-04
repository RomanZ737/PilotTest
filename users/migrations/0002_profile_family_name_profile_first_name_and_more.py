# Generated by Django 4.1.7 on 2023-03-03 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='family_name',
            field=models.CharField(default=None, max_length=500, verbose_name='Фамилия'),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_name',
            field=models.CharField(default=None, max_length=500, verbose_name='Имя'),
        ),
        migrations.AddField(
            model_name='profile',
            name='middle_name',
            field=models.CharField(default=None, max_length=500, verbose_name='Отчество'),
        ),
    ]
