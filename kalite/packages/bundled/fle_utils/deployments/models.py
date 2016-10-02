from django.db import models
from markupfield.fields import MarkupField

# Create your models here.
class Deployment(models.Model):
	title = models.CharField(max_length=250)
	latitude = models.DecimalField(max_digits=5, decimal_places=3)
	longitude = models.DecimalField(max_digits=6, decimal_places=3)
	user_story = MarkupField()
