from django.contrib import admin
from .models import FloodInformation, StationInformation

@admin.register(FloodInformation)
class FloodInformationAdmin(admin.ModelAdmin):
    list_display = ('eventid', 'gaugeid', 'start_date', 'end_date', 'peak_flood_level_m', 'flood_type')
    list_filter = ('flood_type', 'gaugeid')
    search_fields = ('eventid', 'gaugeid')
    ordering = ('-start_date',)
    date_hierarchy = 'start_date'

@admin.register(StationInformation)
class StationInformationAdmin(admin.ModelAdmin):
    list_display = ('gaugeid', 'station_name', 'river_basin', 'state', 'warning_level', 'danger_level', 'reliability')
    list_filter = ('state', 'river_basin', 'reliability')
    search_fields = ('camels_gid', 'station_name', 'river_name_tributory_subtributory')
    ordering = ('state', 'station_name')