from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_not_zero(value):
    if value == 0:
        raise ValidationError(
            _('Количество попыток не может равняться 0'),
            params={'value': value},
        )


# Проверка максимального размера загружаемого файла
def file_size(value):
    filesize = value.size
    if filesize > 2097152:
        raise ValidationError('Превышен максимальный размер файла 2MB')
    else:
        return value


# Валидатор для формы NewTestFormName - проверят уникальность имени теста
def similar_test_name(value):
    test_name = TestConstructor.objects.filter(name=value)
    if len(test_name) > 0:
        raise ValidationError('Тест с таким именем уже существует')
