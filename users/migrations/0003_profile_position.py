# Generated by Django 4.1.7 on 2023-03-03 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_family_name_profile_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='position',
            field=models.CharField(default=None, max_length=500, verbose_name='Должность'),
        ),
    ]
