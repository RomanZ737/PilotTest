# Generated by Django 4.1.7 on 2023-03-03 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_profile_position'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='position',
        ),
    ]
