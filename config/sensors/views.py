from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import IrrigationNode


@login_required
def sensor_latest_readings(request, project_id):
    """
    API endpoint polled every 30s by the frontend.
    Returns latest reading for every active node in this project.
    """
    nodes = IrrigationNode.objects.filter(
        project_id=project_id,
        is_active=True
    ).select_related('farm_boundary')

    data = []
    for node in nodes:
        latest = node.get_latest_reading()
        data.append({
            'sensor_id': node.id,
            'name': node.name,
            'device_id': node.device_id,
            'status': node.status,
            'battery_level': node.battery_level,
            'temperature': latest.temperature if latest else None,
            'humidity': latest.humidity if latest else None,
            'soil_moisture': latest.soil_moisture if latest else None,
            'salinity': latest.salinity if latest else None,
            'ec': latest.ec if latest else None,
            'rainfall': latest.rainfall if latest else None,
            'wind_speed': latest.wind_speed if latest else None,
            'timestamp': latest.timestamp.isoformat() if latest else None,
        })

    return JsonResponse(data, safe=False)