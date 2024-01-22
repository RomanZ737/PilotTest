from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserChangeLog
from django.core.paginator import Paginator
from common import group_required
from django.db.models.functions import Concat
from functools import reduce
from choices import ACTypeP, LogDescription
from django.db.models import Q
from django.contrib.auth.models import User, Group

import operator



@login_required
@group_required('KRS')
def user_log(request):
    ac_types_list = ACTypeP.values  # Список типов ВС для фильтра
    ac_types_list.append('Все')
    event_list = LogDescription.values # Список событий гола
    event_list.append('Все')
    krs_instances = User.objects.filter(groups__name='KRS').order_by(
        'last_name')  # Вынимаем список объектов группы KRS для выбора email адресов
    # Создаём список КРС
    krs_list = []
    for krs_user in krs_instances:
        krs_list.append(krs_user.profile.family_name + ' ' + krs_user.profile.first_name[0] + '.'
                        + krs_user.profile.middle_name[0] + '.')
    krs_list.append('Все')
    # print('KRS_LIST', krs_list)
    # print('filter_input: ', request.GET)
    no_search_result = False
    event_list_instances = UserChangeLog.objects.all().order_by('-timestamp')

    if "user_search" in request.GET:
        user_search_input = request.GET.get("user_search")
        if len(user_search_input) > 0:
            query_db_fields = ['user_changed__profile__family_name', 'user_changed__profile__first_name',
                               'user_changed__profile__middle_name']
            query_words = user_search_input.split()
            event_list_instances = event_list_instances. \
                    annotate(full_name=Concat(*query_db_fields)). \
                    filter(reduce(operator.and_, [Q(full_name__icontains=w) for w in query_words]))

        if len(event_list_instances) > 0: # Если есть результаты поиска
            if 'ac_type_filter' in request.GET: # Если введён фильтр
                ac_type_filter = ''
                event_filter = ''
                krs_filter = ''
                if request.GET.get('ac_type_filter') != 'Все':
                    ac_type_filter = request.GET.get('ac_type_filter')
                if request.GET.get('event_filter') != 'Все':
                    event_filter = request.GET.get('event_filter')
                if request.GET.get('krs_filter') != 'Все':
                    krs_filter = request.GET.get('krs_filter')
                event_list_instances = event_list_instances.filter(user_changed__profile__ac_type__contains=ac_type_filter,
                    description__contains=event_filter,
                    user_done__contains=krs_filter)
                if len(event_list_instances) > 0:  # Если есть результаты поиска
                    paginator = Paginator(event_list_instances, 30)
                    page_number = request.GET.get('page', 1)
                    event_list_pages = paginator.page(page_number)
                    context = {'results': event_list_pages, 'no_search_results': no_search_result,
                               'user_search_input': user_search_input, 'ac_types': ac_types_list,
                               'event_list': event_list, 'krs_instances': krs_list,
                               'ac_type_filter': ac_type_filter, 'event_filter': event_filter,
                               'krs_filter': krs_filter}
                    return render(request, 'user_log.html', context=context)
                else:
                    # Если нет результатов поиска с использованием фильтра
                    results = f'Записи по запросу не найдены'
                    no_search_result = True
                    context = {'results': results, 'no_search_results': no_search_result,
                               'ac_types': ac_types_list, 'event_list': event_list,
                               'krs_instances': krs_list, 'user_search_input': user_search_input}
                    return render(request, 'user_log.html', context=context)
            else:
                paginator = Paginator(event_list_instances, 30)
                page_number = request.GET.get('page', 1)
                event_list_pages = paginator.page(page_number)
                context = {'results': event_list_pages, 'no_search_results': no_search_result,
                           'user_search_input': user_search_input,
                           'ac_types': ac_types_list, 'event_list': event_list,
                           'krs_instances': krs_list}
                return render(request, 'user_log.html', context=context)
        else: # Если нет результатов поиска без фильра
            results = f'Пилоты по запросу "{user_search_input}" не найдены'
            no_search_result = True
            context = {'results': results, 'no_search_results': no_search_result,
                       'ac_types': ac_types_list, 'event_list': event_list,
                       'krs_instances': krs_list, 'user_search_input': user_search_input}
            return render(request, 'user_log.html', context=context)
    else:
        paginator = Paginator(event_list_instances, 30)
        page_number = request.GET.get('page', 1)
        event_list_pages = paginator.page(page_number)
        context = {'results': event_list_pages, 'no_search_results': no_search_result,
                   'ac_types': ac_types_list, 'event_list': event_list,
                   'krs_instances': krs_list}
        return render(request, 'user_log.html', context=context)


