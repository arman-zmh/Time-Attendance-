from django.db import models

class Staff(models.Model):
    name = models.CharField(max_length=255)
    personal_id = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    position = models.CharField(max_length=255)