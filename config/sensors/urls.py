from django.urls import path
from . import views

app_name = 'sensors'

urlpatterns = [
    path(
        'api/projects/<int:project_id>/sensors/latest/',
        views.sensor_latest_readings,
        name='sensor_latest_readings'
    ),
    path(
        'api/client/dashboard/',
        views.client_dashboard_api,
        name='client_dashboard'
    ),
]