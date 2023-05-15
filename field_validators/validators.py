from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_not_zero(value):
    if value == 0:
        raise ValidationError(
            _('Количество попыток не может равняться 0'),
            params={'value': value},
        )
