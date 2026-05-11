from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

# added by me
from django.views.decorators.http import require_http_methods
from django.contrib.gis.geos import Point
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# tell here 
from .models import IrrigationNode, NodeAlert
from project_management.models import Camera, FarmBoundary


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


# added by me 
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_irrigation_node(request, project_id):
    """
    API endpoint to add an irrigation node to an existing project.
    """
    try:
        device_id = (request.data.get('device_id') or '').strip()
        name = (request.data.get('name') or '').strip()
        node_type = request.data.get('node_type') or 'bme280_soil'
        description = (request.data.get('description') or '').strip()
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        farm_boundary_id = request.data.get('farm_boundary_id')

        if not device_id:
            return Response({'success': False, 'error': 'Device ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not name:
            return Response({'success': False, 'error': 'Node name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if node_type not in dict(IrrigationNode.NODE_TYPES):
            return Response({'success': False, 'error': 'Invalid node type'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat = float(latitude)
            lng = float(longitude)
        except (TypeError, ValueError):
            return Response({'success': False, 'error': 'Valid latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

        point = Point(lng, lat, srid=4326)
        boundaries = FarmBoundary.objects.filter(
            project_id=project_id,
            is_active=True,
            boundary__isnull=False
        )

        # Allow placing nodes outside boundaries
        farm_boundary = boundaries.filter(boundary__contains=point).first()

        if farm_boundary is None:
            # Allow placing nodes outside boundaries
            return Response({
                'success': False,
                'error': 'Place the node inside an existing farm boundary'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        '''
        if farm_boundary is None:
        return Response({'success': False, 'error': 'Project has no active farm boundary'}, status=status.HTTP_400_BAD_REQUEST)'''
        # modified by me to allow placing nodes outside boundaries
        if farm_boundary_id and int(farm_boundary_id) != farm_boundary.id:
            return Response({
                'success': False,
                'error': 'Selected location does not match the farm boundary'
            }, status=status.HTTP_400_BAD_REQUEST)

        node = IrrigationNode.objects.create(
            project_id=project_id,
            farm_boundary=farm_boundary,
            device_id=device_id,
            name=name,
            node_type=node_type,
            description=description,
            location=point,
        )

        return Response({
            'success': True,
            'message': f'Node "{node.name}" added successfully',
            'node': {
                'id': node.id,
                'name': node.name,
                'device_id': node.device_id,
                'node_type': node.node_type,
                'node_type_display': node.get_node_type_display(),
                'status': node.status,
                'battery_level': node.battery_level,
                'farm_boundary_id': farm_boundary.id,
                'latitude': node.location.y,
                'longitude': node.location.x,
                'last_reading': None,
            }
        }, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response({
            'success': False,
            'error': 'A node with this Device ID already exists in this project'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_camera(request, project_id):
    """
    API endpoint to add a camera to an existing project.
    Cameras may be placed inside or outside farm boundaries.
    """
    try:
        camera_type = request.data.get('camera_type') or 'ip'
        description = (request.data.get('description') or '').strip()
        ip_address = (request.data.get('ip_address') or '').strip() or None
        port = request.data.get('port')
        cellular_identifier = (request.data.get('cellular_identifier') or '').strip() or None
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        farm_boundary_id = request.data.get('farm_boundary_id')

        if camera_type not in dict(Camera.CAMERA_TYPES):
            return Response({'success': False, 'error': 'Invalid camera type'}, status=status.HTTP_400_BAD_REQUEST)

        if camera_type == 'ip':
            if not ip_address:
                return Response({'success': False, 'error': 'IP address is required for IP cameras'}, status=status.HTTP_400_BAD_REQUEST)
            if not port:
                return Response({'success': False, 'error': 'Port is required for IP cameras'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                port = int(port)
            except (TypeError, ValueError):
                return Response({'success': False, 'error': 'Port must be a number'}, status=status.HTTP_400_BAD_REQUEST)
            if port < 1 or port > 65535:
                return Response({'success': False, 'error': 'Port must be between 1 and 65535'}, status=status.HTTP_400_BAD_REQUEST)
            cellular_identifier = None
        else:
            if not cellular_identifier:
                return Response({'success': False, 'error': 'Cellular identifier is required'}, status=status.HTTP_400_BAD_REQUEST)
            ip_address = None
            port = None

        try:
            lat = float(latitude)
            lng = float(longitude)
        except (TypeError, ValueError):
            return Response({'success': False, 'error': 'Valid latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

        point = Point(lng, lat, srid=4326)
        boundaries = FarmBoundary.objects.filter(
            project_id=project_id,
            is_active=True,
            boundary__isnull=False
        )

        farm_boundary = None
        if farm_boundary_id:
            farm_boundary = boundaries.filter(id=farm_boundary_id).first()

        if farm_boundary is None:
            farm_boundary = boundaries.filter(boundary__contains=point).first()

        if farm_boundary is None:
            farm_boundary = boundaries.first()

        if farm_boundary is None:
            return Response({'success': False, 'error': 'Project has no active farm boundary'}, status=status.HTTP_400_BAD_REQUEST)

        camera = Camera.objects.create(
            project_id=project_id,
            farm_boundary=farm_boundary,
            camera_type=camera_type,
            description=description,
            ip_address=ip_address,
            port=port,
            cellular_identifier=cellular_identifier,
            location=point,
        )

        return Response({
            'success': True,
            'message': f'Camera #{camera.id} added successfully',
            'camera': {
                'id': camera.id,
                'farm_boundary_id': farm_boundary.id,
                'camera_type': camera.camera_type,
                'description': camera.description,
                'latitude': camera.location.y,
                'longitude': camera.location.x,
                'connection_info': camera.get_connection_string(),
                'is_within_boundary': camera.is_within_farm_boundary(),
                'created_at': camera.created_at.isoformat(),
                'fire_risk': None,
            }
        }, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response({
            'success': False,
            'error': 'A camera with this identifier already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


# tell here

@login_required
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_irrigation_node(request, node_id):
    """
    API endpoint to delete an irrigation node.
    Only the owner/authorized users can delete.
    """
    try:
        node = get_object_or_404(IrrigationNode, id=node_id)
        
        # Check if user has permission to delete (optional - add your permission logic)
        # You can add permission checks here if needed
        # if node.project.owner != request.user:
        #     return JsonResponse({'error': 'Permission denied'}, status=403)
        
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
    
