# Generated by Django 4.1.7 on 2023-02-26 13:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quize737', '0009_quizeresults_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizeresults',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='Время и дата теста'),
        ),
    ]