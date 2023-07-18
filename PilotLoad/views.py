from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from users.models import Profile
from django.contrib.auth.decorators import login_required
import pymysql  # модуль работы с MySQL

from pymysql.cursors import DictCursor

from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)

@login_required
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
    request = f'SELECT DISTINCT firstName, lastName, middleName, position, workEmail FROM personal WHERE position LIKE "%Пилот-инструктор%" OR position LIKE "%Командир ВС%" OR position LIKE "%Второй пилот%" OR position LIKE "%Пилот инструктор%" OR position LIKE "%пилот-инструктор%" '
    # request = f'SELECT firstName, lastName, middleName, position, workEmail FROM personal WHERE personnelId = 6460'

    cur.execute(request)
    data = cur.fetchall()

    # print('DATA:', data)

    for pilot in data:
        print('Создаём:', pilot)

        # Данные по умолчанию
        group_name = 'Unknown'
        position = 'ВП'
        ac_type = 'ANY'

        # Выделяем первую часть e-mail
        if pilot['workEmail']:
            index = pilot['workEmail'].find('@')
            username = pilot['workEmail'][:index]
            password = username

            #  Выясняем квалификацию и группу пользователя
            if 'Командир' in pilot['position']:
                position = 'КВС'
                if 'Б-737' in pilot['position'] or 'Боинг-737' in pilot['position']:
                    print('HEREEEEE')
                    group_name = 'КВС B737'
                    ac_type = 'B737'
                elif 'А-321' in pilot['position']:
                    group_name = 'КВС A32X'
                    ac_type = 'A32X'
                elif 'А-330' in pilot['position']:
                    group_name = 'КВС A33X'
                    ac_type = 'A33X'
                elif 'Боинг-777' or 'Б-777' in pilot['position']:
                    group_name = 'КВС B777'
                    ac_type = 'B777'

            elif 'Второй пилот' in pilot['position']:
                position = 'ВП'
                if 'Б-737' in pilot['position'] or 'Боинг-737' in pilot['position']:
                    group_name = 'ВП B737'
                    ac_type = 'B737'
                elif 'А-321' in pilot['position']:
                    group_name = 'ВП A32X'
                    ac_type = 'A33X'
                elif 'А-330' in pilot['position']:
                    group_name = 'ВП A33X'
                elif 'Боинг-777' or 'Б-777' in pilot['position']:
                    group_name = 'ВП B777'
                    ac_type = 'B777'

            elif 'Пилот-инструктор' or 'Пилот инструктор' or 'Пилот – инструктор' in pilot['position']:
                position = 'ПИ'
                if 'Б-737' in pilot['position'] or 'Боинг-737' in pilot['position']:
                    group_name = 'ПИ B737'
                    ac_type = 'B737'
                elif 'А-321' in pilot['position']:
                    group_name = 'ПИ A32X'
                    ac_type = 'B737'
                elif 'А-330' in pilot['position']:
                    group_name = 'ПИ A33X'
                    ac_type = 'A33X'
                elif 'Боинг-777' or 'Б-777' in pilot['position']:
                    group_name = 'ПИ B777'
                    ac_type = 'B777'

            first_name = pilot['firstName']
            last_name = pilot['lastName']
            middle_name = pilot['middleName']
            email = pilot['workEmail']

            print('username:', username, 'pass:', password, 'group:', group_name, 'ac_type', ac_type)

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
