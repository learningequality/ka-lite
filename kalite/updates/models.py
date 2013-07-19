from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class UpdateProcessLog(models.Model):
    process_name = models.CharField(verbose_name="process name", max_length=100)
    process_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0)
    stage_name = models.CharField(verbose_name="stage name", max_length=100)
    stage_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0)
    notes = models.TextField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    completed = models.BooleanField(default=False)

