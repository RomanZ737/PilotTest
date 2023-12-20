from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserChangeLog


@login_required
def user_log(request):
    event_list_instances = UserChangeLog.objects.all().order_by('-timestamp')
    paginator = Paginator(event_list_instances, 30)
    page_number = request.GET.get('page', 1)
    event_list_pages = paginator.page(page_number)
    context = {'results': event_list_pages}
    return render(request, 'user_log.html', context=context)

