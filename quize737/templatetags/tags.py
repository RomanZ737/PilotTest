from django import template
import random
import datetime
from django.db.models import Q, F
from django.core.exceptions import ObjectDoesNotExist
from users.models import UserTests
from django.contrib.auth.models import User

register = template.Library()


@register.filter(name='dict_keys')
def dict_to_keys_val(dict):
    array = []
    for key in dict:
        array.append(key.id)
    return array


@register.filter(name='has_group')
def has_group(user, group_name):
    str_new = ''.join(group_name).split(',')
    return user.groups.filter(name__in=str_new).exists()


@register.filter(name='random_loop')
def shuffle(arg):
    aux = list(arg)[:]
    random.shuffle(aux)
    return aux


@register.simple_tag(takes_context=True)
def check_test_date(context, date):
    return datetime.datetime.now() > date


@register.simple_tag(takes_context=True)
def check_test_num_try(context, one, two):
    print('one: ', one)
    print('one: ', two)
    if one <= 0:
        try:
            UserTests.objects.get((Q(num_try__lte=0) &
                                   Q(user__quizeresults__in_progress=False) &
                                   Q(results_id=F('user__quizeresults__id'))), id=two)
            return True
        except ObjectDoesNotExist:
            return False


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """

    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()


#  Вынимаем значение из словаря по ключу (в переменной) в template
@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    else:
        return None
