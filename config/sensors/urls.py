from django.urls import path
from . import views

app_name = 'sensors'

urlpatterns = [
    path(
        'api/projects/<int:project_id>/sensors/latest/',
        views.sensor_latest_readings,
        name='sensor_latest_readings'
    ),

    # added by me
    path(
        'api/projects/<int:project_id>/irrigation-nodes/add/',
        views.add_irrigation_node,
        name='add_irrigation_node'
    ),
    path(
        'api/projects/<int:project_id>/cameras/add/',
        views.add_camera,
        name='add_camera'
    ),

    # Endpoint to delete an irrigation node
    path(
        'api/client/dashboard/',
        views.client_dashboard_api,
        name='client_dashboard' ) ,
    path(
        'api/irrigation-nodes/<int:node_id>/delete/',
        views.delete_irrigation_node,
        name='delete_irrigation_node'
    ),
]
