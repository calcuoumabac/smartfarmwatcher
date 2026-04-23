# Django core imports
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# Local app imports
from project_management.models import Project, Camera
from detection_management.models import Detection

# Python standard library
from datetime import timedelta


@login_required
def dashboard_view(request):
    """Main dashboard view with latest project and detection"""
    
    # Get user's projects
    if request.user.user_type == 'supervisor':
        user_projects = Project.objects.filter(created_by=request.user, is_active=True)
    else:
        # For clients, get projects they have access to
        user_projects = Project.objects.filter(
            user_roles__user=request.user,
            is_active=True
        ).distinct()
    
    # Get latest project
    latest_project = user_projects.order_by('-created_at').first()
    
    # Add statistics to the latest project if it exists
    if latest_project:
        latest_project.total_boundaries = latest_project.get_total_farm_boundaries()
        latest_project.total_cameras = latest_project.get_total_cameras()
        latest_project.total_environment_nodes = latest_project.get_total_environment_nodes() # new
        latest_project.total_water_nodes = latest_project.get_total_water_nodes() # new
        latest_project.total_detections = Detection.objects.filter(
            camera__project=latest_project
        ).count()
    
    # Get latest detection from user's projects
    latest_detection = Detection.objects.filter(
        camera__project__in=user_projects
    ).select_related(
        'camera', 'camera__project', 'camera__farm_boundary', 'detection_type'
    ).order_by('-detected_at').first()
    
    # Add confidence percentage if detection exists
    if latest_detection:
        latest_detection.confidence_percentage = latest_detection.confidence_score * 100
    
    # Get statistics
    project_count = user_projects.count()
    
    # Get camera count
    camera_count = Camera.objects.filter(
        project__in=user_projects,
        is_active=True
    ).count()

    # added by me 
    from sensors.models import IrrigationNode
    environment_node_count = IrrigationNode.objects.filter(
        project__in=user_projects,
        is_active=True,
        node_type='bme280_soil'
    ).count()
    
    water_node_count = IrrigationNode.objects.filter(
        project__in=user_projects,
        is_active=True,
        node_type='salinity'
    ).count()
    
    # Get detection count for today
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    detection_count = Detection.objects.filter(
        camera__project__in=user_projects,
        detected_at__gte=today
    ).count()
    
    # Get alert count (you can customize this based on your alert system)
    alert_count = Detection.objects.filter(
        camera__project__in=user_projects,
        is_false_positive=False,
        detected_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    context = {
        'latest_project': latest_project,
        'latest_detection': latest_detection,
        'project_count': project_count,
        'camera_count': camera_count,
        'detection_count': detection_count,
        'alert_count': alert_count,
        'environment_node_count': environment_node_count,  # ← new
        'water_node_count': water_node_count, # ← new
    }
    
    # Route clients to mobile app invitation page
    if request.user.user_type == 'client':
        return render(request, 'dashboard/dashboard_client.html', context)
    else:
        # Supervisors get the regular dashboard
        return render(request, 'dashboard/dashboard_supervisor.html', context)

@login_required
def mobile_app_view(request):
    """Dedicated mobile app download page - accessible to all users"""
    
    # Get user's projects for basic stats (optional - can be used for personalization)
    if request.user.user_type == 'supervisor':
        user_projects = Project.objects.filter(created_by=request.user, is_active=True)
    else:
        user_projects = Project.objects.filter(
            user_roles__user=request.user,
            is_active=True
        ).distinct()
    
    # Basic stats (optional)
    project_count = user_projects.count()
    camera_count = Camera.objects.filter(
        project__in=user_projects,
        is_active=True
    ).count()
    
    context = {
        'project_count': project_count,
        'camera_count': camera_count,
        'user_projects': user_projects,
    }
    
    return render(request, 'dashboard/download_mobile_app.html', context)