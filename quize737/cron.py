import datetime
import common

from django_cron import CronJobBase, Schedule
from users.models import TestExpired, UserTests
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)

#  https://www.section.io/engineering-education/automating-jobs-schedule-with-django-cron-in-python/

now = datetime.datetime.now().date()

five_day_before = datetime.datetime.now().date() + datetime.timedelta(days=common.days_left_notify)

# Проверка просроченных тестов
class MyCronJob(CronJobBase):
    """Если до конца срока сдачи теста осталось 5 дней и менее, будет отправлено уведомление пользователю.
    Если срок сдачи уже истёк, будет отправлено уведомление КРС и пользователю"""
    RUN_EVERY_MINS = 3
    #RUN_EVERY_MINS = 720  # every 12 hors
    RUN_AT_TIMES = ['08:00']#, '14:00', '23:15']
    #RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_at_times=RUN_AT_TIMES, run_every_mins=RUN_EVERY_MINS)#, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = 'quize737.my_cron_job'  # a unique code

    def do(self):
        user_test_list = UserTests.objects.all()
        for user_test in user_test_list:
            test_date_before = user_test.date_before.date()
            if test_date_before < now:
                user_test_instance = UserTests.objects.get(user=user_test.user, test_name=user_test.test_name)
                try:
                    TestExpired.objects.get(user=user_test.user, test=user_test_instance)
                    tets_inst = TestExpired.objects.get(user=user_test.user, test=user_test_instance)
                    tets_inst.days_left = 0
                    tets_inst.save()
                except Exception:
                    TestExpired.objects.create(user=user_test.user,
                                               test=user_test,
                                               days_left=0
                                               )
                # Отсылаем письмо руководству
                email_list = user_test_instance.test_name.email_to_send
                subject = f'Пилот {user_test.user.profile.family_name} {(user_test.user.profile.first_name)[0]}. {(user_test.user.profile.middle_name)[0]}. ПРОСРОЧИЛ тест'
                message = f'<p style="font-size: 20px;"><b>{user_test.user.profile.family_name} {user_test.user.profile.first_name} {user_test.user.profile.middle_name}</b></p><br>' \
                          f'<p style="color: rgb(142, 23, 11); font-size: 20px;"><b>ПРОСРОЧИЛ ТЕСТ</b></p>' \
                          f'<p style="font-size: 15px;">Название теста: <b>{user_test.test_name}</b></p>' \
                          f'<p style="font-size: 15px;">Дата: <b>{user_test.date_before.strftime("%d.%m.%Y")}</b></p>' \
                          f'<p>email: {email_list}</p>'

                #email_list = user_test_instance.test_name.email_to_send
                email_msg = {'subject': subject, 'message': message, 'to': email_list}
                common.send_email(user_test, email_msg)

                #  Отправляем письмо пользователю если до истечения срока сдачи N дней или менее (письмо один раз)
                subject = f"Срок сдачи Теста '{user_test.test_name}' Истекает"
                message = f"<p style='font-size: 25px;'><b>Уважаемый, {user_test.user.profile.first_name} {user_test.user.profile.middle_name}.</b></p><br>" \
                          f"<p style='font-size: 20px;'>Истёк срок сдачи Теста <b>'{user_test.test_name}'</b></p>" \
                          f"<p style='font-size: 20px;'>Тест необходимо выполнить до <b>{user_test.date_before.strftime('%d.%m.%Y')}</b></p>" \
                          f"<p style='font-size: 20px;'>На портале {config('SITE_URL', default='')}</p>" \
                          f"<br>" \
                          f"<p style='font-size: 20px;'>По умолчанию логин для входа: Ваш email до знака @, пароль такой же</p>" \
                          f"<p style='font-size: 20px;'>Рекомендуем сменить пароль после первого входа</p>"

                email_msg = {'subject': subject, 'message': message, 'to': 'pomanz@mail.ru'}#user_test.user.email}
                common.send_email(user_test, email_msg)

            elif now < test_date_before <= five_day_before:
                days_left = (test_date_before - now).days
                print(f'{days_left} DAY LEFT:', user_test.user.last_name)
                try:
                    user_test_instance = UserTests.objects.get(user=user_test.user, test_name=user_test.test_name)
                    TestExpired.objects.get(user=user_test.user, test=user_test_instance)
                    tets_inst = TestExpired.objects.get(user=user_test.user, test=user_test_instance)
                    tets_inst.days_left = days_left
                    tets_inst.save()
                except Exception:
                    TestExpired.objects.create(user=user_test.user,
                                               test=user_test,
                                               days_left=days_left
                                               )

                    #  Отправляем письмо пользователю если до истечения срока сдачи N дней или менее (письмо один раз)
                    subject = f"Срок сдачи Теста '{user_test.test_name}' Истекает"
                    message = f"<p style='font-size: 25px;'><b>Уважаемый, {user_test.user.profile.first_name} {user_test.user.profile.middle_name}.</b></p><br>" \
                              f"<p style='font-size: 20px;'>Дней до истечения срока сдачи Теста '{user_test.test_name}': <b>{days_left} </b></p>" \
                              f"<p style='font-size: 20px;'>Тест необходимо выполнить до <b>{user_test.date_before.strftime('%d.%m.%Y')}</b></p>" \
                              f"<p style='font-size: 20px;'>На портале {config('SITE_URL', default='')}</p>" \
                              f"<br>" \
                              f"<p style='font-size: 20px;'>По умолчанию логин для входа: Ваш email до знака @, пароль такой же</p>" \
                              f"<p style='font-size: 20px;'>Рекомендуем сменить пароль после первого входа</p>"

                    email_msg = {'subject': subject, 'message': message, 'to': 'pomanz@mail.ru'}#user_test.user.email}
                    common.send_email(user_test, email_msg)
