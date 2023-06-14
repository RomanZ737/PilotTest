from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from users.models import Profile
import pymysql  # модуль работы с MySQL

from pymysql.cursors import DictCursor

from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)


def pilotload(request):
    connection = pymysql.connect(  # Коннектимся к базе MySQL
        host=config('ip_mysql_tech', default=''),
        user=config("SQL_usrID_tech", default=''),
        password=config('SQL_password_tech', default=''),
        db=config('SQL_DB_tech', default=''),
        charset='utf8mb4',
        cursorclass=DictCursor  # Курсор будет возвращать значения в виде словарей
    )
    cur = connection.cursor()  # Создаём курсор SQL
    # формируем запрос для пользовательских данных
    request = f'SELECT firstName, lastName, middleName, position, workEmail FROM personal WHERE position LIKE "%Боинг-737%" OR position LIKE "%Б-737%"'
    # request = f'SELECT firstName, lastName, middleName, position, workEmail FROM personal WHERE personnelId = 6460'

    cur.execute(request)
    data = cur.fetchall()

    # print('DATA:', data)

    for pilot in data:
        print('Создаём:', pilot)
        # Выделяем первую часть e-mail
        if pilot['workEmail']:
            index = pilot['workEmail'].find('@')
            username = pilot['workEmail'][:index]
            password = username
            if 'Командир' in pilot['position']:
                group_name = 'КВС B737'
                position = 'КВС'
            elif 'Второй пилот' in pilot['position']:
                group_name = 'ВП B737'
                position = 'ВП'
            elif 'Пилот инструктор' in pilot['position']:
                group_name = 'ПИ B737'
                position = 'ПИ'
            else:
                group_name = 'Unknown'
                position = 'ВП'

            ac_type = 'B737'
            first_name = pilot['firstName']
            last_name = pilot['lastName']
            middle_name = pilot['middleName']
            email = pilot['workEmail']

            print('username:', username, 'pass:', password)

            try:
                User.objects.get(username=username)
                print('Пользователь Существует')
            except Exception:
                new_user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password,
                )
                group = Group.objects.get(name=group_name)
                new_user.groups.add(group)

                Profile.objects.create(user=new_user,
                                       family_name=last_name,
                                       first_name=first_name,
                                       middle_name=middle_name,
                                       position=position,
                                       ac_type=ac_type
                                       )
        else:
            continue

    return redirect('quize737:start')
