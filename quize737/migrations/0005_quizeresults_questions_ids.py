# Generated by Django 4.1.6 on 2023-02-16 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quize737', '0004_quizeresults_alter_quizeset_quize_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizeresults',
            name='questions_ids',
            field=models.CharField(max_length=200, null=True, verbose_name='Номера вопросов'),
        ),
    ]