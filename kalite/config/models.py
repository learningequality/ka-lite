from django.db import models
from utils import convert
import logging

# Use this so we don't have to read from database every time

_settings_cache = {}

class Settings(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    value = models.TextField(blank=True)
    datatype = models.CharField(max_length=10, default="str")
    
    
    @staticmethod
    def set(name, value):
        # Write to the database
        setting = Settings(name=name, value=str(value), datatype=value.__class__.__name__)
        setting.save()
        
        # Save to the settings cache
        _settings_cache[name] = value
        
    @staticmethod
    def get(name, default=""):
        try:
            setting = Settings.objects.get(name=name)
            if name in _settings_cache:
                logging.debug("[0] Got from cache: Setting: name [%s] type [%s] value [%s]"%(name, setting.datatype, setting.value))
                return _settings_cache[name]
            else:
                logging.debug("[1] Got from DB: Setting: name [%s] type [%s] value [%s]"%(name, setting.datatype, setting.value))
                value = convert.convert_value(setting.value, setting.datatype)
                _settings_cache[name] = value
                return value
                
        except Settings.DoesNotExist:
            return default
    
    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"
