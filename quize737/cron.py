from django_cron import CronJobBase, Schedule
import requests
from users.models import TestExpired
import django_cron



#  https://www.section.io/engineering-education/automating-jobs-schedule-with-django-cron-in-python/


class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 5 # every 5 minutes
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = 'quize737.my_cron_job'    # a unique code

    # def do(self):
    #     user_test_list =