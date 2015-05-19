from django.db import models


class AssessmentItem(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    item_data = models.TextField()  # A serialized JSON blob
    author_names = models.CharField(max_length=200)  # A serialized JSON list