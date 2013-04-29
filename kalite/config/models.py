from django.db import models
from utils import convert

class Settings(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    value = models.TextField(blank=True)
    datatype = models.CharField(max_length=10, default="str")
    
    @staticmethod
    def set(name, value):
        setting = Settings(name=name, value=str(value), datatype=value.__class__.__name__)
        setting.save()
        
    @staticmethod
    def get(name, default=""):
        try:
            setting = Settings.objects.get(name=name)
            import logging
            logging.debug("Setting: name [%s] type [%s] value [%s]"%(name, setting.datatype, setting.value))
#            if name=="CENTRAL_SERVER":
#                import pdb; pdb.set_trace()
            return convert.convert_value(setting.value, setting.datatype)
        except Settings.DoesNotExist:
            return default
    
    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"
