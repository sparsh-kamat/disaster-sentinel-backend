# Generated by Django 5.1.5 on 2025-05-06 17:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_otpstorage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='city',
            new_name='district',
        ),
    ]
