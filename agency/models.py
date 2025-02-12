from django.db import models

# Create your models here.
# i have already created and populated the table like the follow :
# CREATE TABLE IF NOT EXISTS "agency_details" (
#     "id" INT PRIMARY KEY,
#     "name" TEXT,
#     "address" TEXT,
#     "state" TEXT,
#     "district" TEXT,
#     "email" TEXT,
#     "phone" TEXT,
#     "category" TEXT
# );

class ExistingAgencies(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    category = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'agency_details'
        managed = False
    
    def __str__(self):
        return self.name