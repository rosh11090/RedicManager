from .models import *
from django.contrib import admin
import json


class KVPAdmin(admin.ModelAdmin):
    class Meta:
        fields = ('key', 'value', 'value_type')

    def save_model(self, request, obj, form, change):
        redis_dict = GlobalDictionary.objects.get(name='redis')
        obj.dictionary = redis_dict
        obj.save()

# admin.site.register(GlobalDictionary)
admin.site.register(KeyValuePair)