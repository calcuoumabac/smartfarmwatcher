from django.db import models
from django.contrib.gis.db import models as gis_models

class IrrigationNode(models.Model):
    NODE_TYPES = [
        ('bme280_soil', 'BME280 + Soil Moisture'),
        ('salinity',    'Salinity Sensor'),
    ]

    project       = models.ForeignKey('project_management.Project', on_delete=models.CASCADE, related_name='irrigation_nodes')
    farm_boundary = models.ForeignKey('project_management.FarmBoundary', on_delete=models.CASCADE, related_name='irrigation_nodes')
    device_id     = models.CharField(max_length=100, unique=True)
    name          = models.CharField(max_length=100)
    node_type     = models.CharField(max_length=20, choices=NODE_TYPES, default='bme280_soil')
    location      = gis_models.PointField(srid=4326, null=True, blank=True)
    description   = models.TextField(null=True, blank=True)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.device_id}) - {self.project.name}"

    def get_latest_reading(self):
        return self.readings.order_by('-timestamp').first()


class SensorReading(models.Model):
    node          = models.ForeignKey(IrrigationNode, on_delete=models.SET_NULL, null=True, blank=True, related_name='readings')
    device_id     = models.CharField(max_length=100)
    timestamp     = models.DateTimeField()
    temperature   = models.FloatField(null=True, blank=True)
    humidity      = models.FloatField(null=True, blank=True)
    pressure      = models.FloatField(null=True, blank=True)
    soil_moisture = models.FloatField(null=True, blank=True)
    gas_resistance= models.FloatField(null=True, blank=True)
    raw_data      = models.JSONField(default=dict)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device_id', '-timestamp']),
            models.Index(fields=['node', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.device_id} - {self.timestamp}"