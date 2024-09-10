from django.db import models

# Create your models here.
class Dogs(models.Model):
    dog_name = models.CharField(max_length=200)
    is_admin = models.BooleanField()
    def __str__(self):
        return self.dog_name
