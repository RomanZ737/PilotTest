from django.db import models


class Position(models.TextChoices):
    PIC = 'КВС', 'Командир ВС'
    COPILOT = 'ВП', 'Второй пилот'
    INSTRUCTOR = 'ПИ', 'Пилот-инструктор'


#  Выбор типа ВС для профиля пользователя
class ACTypeP(models.TextChoices):
    B737 = 'B737', 'Boeing 737'
    B777 = 'B777', 'Boeing 777'
    A32X = 'A32X', 'Airbus 32X'
    A33X = 'A33X', 'Airbus 33X'


# Выбор типа ВС для создания вопроса
class ACTypeQ(models.TextChoices):
    B737 = 'B737', 'Boeing 737'
    B777 = 'B777', 'Boeing 777'
    A32X = 'A32X', 'Airbus 32X'
    A33X = 'A33X', 'Airbus 33X'
    ANY = 'ANY', 'ANY TYPE'


class LogDescription(models.TextChoices):
    NewTest = 'Назначен тест', 'Пользователю назначен тест'
    NumTry = 'Кол-во попыток', 'Изменено количество попыток'
    DateChange = 'Изм. дата', 'Изменена дата сдачи теста'
    UserData = 'Изм. данных', 'Изменены личные данные Пилота'
    DelTest = 'Удалён Тест', 'У Пилота удалён тест'
    DelUser = 'Удалён Пилот', 'Чётная запись пилота удалена'
    NewUser = 'Добавлен Пилот', 'Добавлена учётная запись пилота'
