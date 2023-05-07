from django.contrib import admin
from .models import QuestionSet, Thems, QuizeSet, QuizeResults, TestConstructor

# Register your models here.
admin.site.register(QuestionSet)
admin.site.register(Thems)
admin.site.register(QuizeSet)
admin.site.register(QuizeResults)
admin.site.register(TestConstructor)