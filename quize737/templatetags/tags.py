from django import template
import random

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='random_loop')
def shuffle(arg):
    #print('args before:', arg)
    aux = list(arg)[:]
    random.shuffle(aux)
    return aux
