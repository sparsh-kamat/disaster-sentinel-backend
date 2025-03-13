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
    warning_level = models.DecimalField(max_digits=18, decimal_places=14)
    danger_level = models.DecimalField(max_digits=7, decimal_places=3)
    station = models.TextField()
    latitude = models.DecimalField(max_digits=6, decimal_places=4)
    longitude = models.DecimalField(max_digits=6, decimal_places=4)
    river_name_tributory_subtributory = models.TextField()
    basin = models.TextField()
    state = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    level_entries = models.IntegerField()
    streamflow_entries = models.IntegerField()
    privacy = models.TextField()
    source_catchment_area = models.DecimalField(max_digits=8, decimal_places=2)
    catchment_area = models.DecimalField(max_digits=20, decimal_places=14)
    area_variation = models.DecimalField(max_digits=19, decimal_places=16)
    reliability = models.TextField()

    class Meta:
        managed = False
        db_table = 'station_information'