# Generated by Django 5.1.5 on 2025-05-06 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missingreport', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='missingpersonreport',
            name='additional_info',
            field=models.TextField(blank=True, help_text='Any other relevant information (optional).', null=True),
        ),
        migrations.AddField(
            model_name='missingpersonreport',
            name='age',
            field=models.PositiveIntegerField(blank=True, help_text='Age of the missing person (optional).', null=True),
        ),
        migrations.AddField(
            model_name='missingpersonreport',
            name='disaster_type',
            field=models.CharField(blank=True, choices=[('Cyclones', 'Cyclones'), ('Earthquakes', 'Earthquakes'), ('Tsunamis', 'Tsunamis'), ('Floods', 'Floods'), ('Landslides', 'Landslides'), ('Fire', 'Fire'), ('Heatwave', 'Heatwave'), ('Other', 'Other')], help_text='Type of disaster associated with the missing person report (optional).', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='missingpersonreport',
            name='district',
            field=models.CharField(blank=True, help_text='District where the person was last seen or resides.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='missingpersonreport',
            name='gender',
            field=models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], help_text='Gender of the missing person (optional).', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='missingpersonreport',
            name='state',
            field=models.CharField(blank=True, help_text='State where the person was last seen or resides.', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='missingpersonreport',
            name='last_seen_location',
            field=models.TextField(help_text="Text description of where and when the person was last seen (from form's lastSeenPlace)."),
        ),
    ]
