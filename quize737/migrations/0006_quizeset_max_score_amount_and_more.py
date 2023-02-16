# Generated by Django 4.1.6 on 2023-02-16 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quize737', '0005_quizeresults_questions_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizeset',
            name='max_score_amount',
            field=models.IntegerField(default=0, help_text='Максимально возможное количество баллов, если в вопроса был указан вес', verbose_name='Максимальное кол-во баллов'),
        ),
        migrations.AlterField(
            model_name='quizeset',
            name='questions_ids',
            field=models.CharField(help_text='Сквозные Номера вопросов сгенерированные пользователю', max_length=200, null=True, verbose_name='Номера вопросов'),
        ),
    ]
