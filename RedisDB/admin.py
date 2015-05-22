from django.contrib import admin
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver

from models import GlobalDictionary, KeyValuePair
from views import RedisMenager


class KVPAdmin(admin.ModelAdmin):
    class Meta:
        fields = ('key', 'value', 'value_type')

    def save_model(self, request, obj, form, change):
        redis_dict = GlobalDictionary.objects.get(name='redis')
        obj.dictionary = redis_dict
        obj.save()

@receiver(pre_save, sender=KeyValuePair)
def redisKey_changed(sender, instance, *args, **kwargs):
    rediscache = RedisMenager()
    rediscache.set(instance.key, instance.value)

@receiver(pre_delete, sender=KeyValuePair)
def redisKey_deleted(sender, instance, *args, **kwargs):
    rediscache = RedisMenager()
    rediscache.delete(instance.key)

admin.site.register(GlobalDictionary)
admin.site.register(KeyValuePair)
