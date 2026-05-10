"""from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import IrrigationNode


@login_required
def sensor_latest_readings(request, project_id):
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


<<<<<<< HEAD
#client api endpoint 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import IrrigationNode, NodeAlert

@login_required
def client_dashboard_api(request):
    #Returns sensor data for all projects the client belongs to.
    user = request.user

    # Get projects this client is assigned to
    projects = user.project_roles.values_list('project', flat=True)

    # Get all active nodes in those projects
    nodes = IrrigationNode.objects.filter(
        project_id__in=projects,
        is_active=True
    ).select_related('project', 'farm_boundary')

    sensor_data = []
    for node in nodes:
        latest = node.get_latest_reading()
        sensor_data.append({
            'node_id': node.id,
            'name': node.name,
            'project': node.project.name,
            'status': node.status,
            'temperature': latest.temperature if latest else None,
            'humidity': latest.humidity if latest else None,
            'soil_moisture': latest.soil_moisture if latest else None,
            'salinity': latest.salinity if latest else None,
            'ec': latest.ec if latest else None,
            'timestamp': latest.timestamp.isoformat() if latest else None,
        })

    # Get unresolved alerts
    alerts = NodeAlert.objects.filter(
        node__project_id__in=projects,
        is_resolved=False
    ).select_related('node').values(
        'id', 'alert_type', 'value', 'unit',
        'node__name', 'created_at'
    )

    return JsonResponse({
        'sensors': sensor_data,
        'alerts': list(alerts),
    }) """ 
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import IrrigationNode, NodeAlert


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sensor_latest_readings(request, project_id):
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

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_dashboard_api(request):
    user = request.user

    projects = user.project_roles.values_list('project', flat=True)

    nodes = IrrigationNode.objects.filter(
        project_id__in=projects,
        is_active=True
    ).select_related('project', 'farm_boundary')

    sensor_data = []
    for node in nodes:
        latest = node.get_latest_reading()
        sensor_data.append({
            'node_id': node.id,
            'name': node.name,
            'node_type': node.node_type,
            'project': node.project.name,
            'status': node.status,
            'temperature': latest.temperature if latest else None,
            'humidity': latest.humidity if latest else None,
            'soil_moisture': latest.soil_moisture if latest else None,
            'salinity': latest.salinity if latest else None,
            'ec': latest.ec if latest else None,
            'timestamp': latest.timestamp.isoformat() if latest else None,
        })

    alerts = NodeAlert.objects.filter(
        node__project_id__in=projects,
        is_resolved=False
    ).select_related('node').values(
        'id', 'alert_type', 'value', 'unit',
        'node__name', 'created_at'
    )

    return Response({
        'sensors': sensor_data,
        'alerts': list(alerts),
    })
=======
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_irrigation_node(request, node_id):
    """
    API endpoint to delete an irrigation node.
    Only authenticated users can delete nodes from their projects.
    """
    try:
        node = get_object_or_404(IrrigationNode, id=node_id)
        
        # Optional: Add permission check if needed
        # if node.project.created_by != request.user:
        #     return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        node_name = node.name
        node.delete()
        
        return Response({
            'success': True,
            'message': f'Node "{node_name}" deleted successfully'
        }, status=status.HTTP_200_OK)
    
    except IrrigationNode.DoesNotExist:
        return Response({
            'error': 'Node not found',
            'success': False
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)
>>>>>>> 370f99ef058c583982c38e48637bf2aa3438e764
