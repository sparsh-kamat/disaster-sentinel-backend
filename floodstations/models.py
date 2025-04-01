from django.db import models

class FloodInformation(models.Model):
    eventid = models.TextField(primary_key=True)
    gaugeid = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    peak_flood_level_m = models.DecimalField(max_digits=7, decimal_places=3)
    peak_fl_date = models.DateTimeField()
    num_peak_fl = models.IntegerField()
    peak_discharge_q_cumec = models.DecimalField(max_digits=7, decimal_places=2)
    peak_discharge_date = models.DateTimeField()
    flood_volume_cumec = models.DecimalField(max_digits=9, decimal_places=2)
    event_duration_days = models.IntegerField()
    time_to_peak_days = models.IntegerField()
    recession_time_day = models.IntegerField()
    flood_type = models.TextField()

    class Meta:
        managed = False
        db_table = 'flood_information'


class StationInformation(models.Model):
    gaugeid = models.IntegerField(primary_key=True)
    indofloods_gid = models.IntegerField()
    station_name = models.TextField()
    river_basin = models.TextField()
    group = models.TextField()
    longitude = models.DecimalField(max_digits=6, decimal_places=4)
    latitude = models.DecimalField(max_digits=6, decimal_places=4)
    warning_level = models.DecimalField(max_digits=17, decimal_places=14)
    danger_level = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    river_name_tributory_subtributory = models.TextField()
    state = models.TextField()
    reliability = models.TextField()
    num_floods = models.IntegerField()
    flood_months = models.TextField()  # Could be JSONField if using PostgreSQL
    flow_availability = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'station_information'