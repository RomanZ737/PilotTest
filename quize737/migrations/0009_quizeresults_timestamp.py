# Generated by Django 4.1.7 on 2023-02-26 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quize737', '0008_quizeresults_total_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizeresults',
            name='timestamp',
            field=models.DateTimeField(null=True, verbose_name='Время и дата теста'),
        ),
    ]
