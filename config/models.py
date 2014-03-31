from django.db import models

class Settings(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    value = models.TextField(blank=True)
    datatype = models.CharField(max_length=10, default="str")

    @staticmethod
    def set(name, value):
        setting = Settings(name=name, value=unicode(value), datatype=value.__class__.__name__)
        setting.save()

    @staticmethod
    def get(name, default=""):
        try:
            setting = Settings.objects.get(name=name)
            if setting.datatype == "int":
                return int(setting.value)
            if setting.datatype == "float":
                return float(setting.value)
            if setting.datatype == "bool":
                return bool(setting.value)
            return setting.value
        except Settings.DoesNotExist:
            return default

    @staticmethod
    def delete(name):
        try:
            setting = Settings.objects.filter(name=name).delete()
        except Settings.DoesNotExist:
            pass

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"