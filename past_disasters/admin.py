from django.contrib import admin

from .models import PastDisaster
# Register your models here.
# from django.db import models

# class PastDisaster(models.Model):
#     latitude = models.DecimalField(max_digits=9, decimal_places=7)
#     longitude = models.DecimalField(max_digits=9, decimal_places=7)
#     title = models.CharField(max_length=255)
#     year = models.IntegerField()
#     month = models.CharField(max_length=20)
#     location = models.CharField(max_length=255)
#     state = models.CharField(max_length=100)
#     disaster_type = models.CharField(max_length=100)
#     total_deaths = models.IntegerField()
#     total_injured = models.IntegerField()
#     total_affected = models.BigIntegerField()
#     loss_inr = models.BigIntegerField()

#     class Meta:
#         db_table = 'past_disasters'  # Use the same table name in the database

#     def __str__(self):
#         return f'{self.title} ({self.year})'


admin.site.register(PastDisaster)