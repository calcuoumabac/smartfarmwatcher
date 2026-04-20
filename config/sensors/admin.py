from django.contrib import admin
from .models import SensorReading

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'timestamp', 'temperature', 'humidity', 'soil_moisture']
    list_filter = ['device_id']
    search_fields = ['device_id']