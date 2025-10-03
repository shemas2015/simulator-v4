from django.urls import path
from . import views

urlpatterns = [
    # REST API endpoints
    path('api/connections/', views.get_connections, name='get_connections'),
    path('api/connections/<str:port>/', views.get_connection_status, name='get_connection_status'),
    path('api/connections/<str:port>/position/', views.update_motor_position, name='update_motor_position'),

    # Server-Sent Events endpoint for real-time updates
    path('api/events/connections/', views.connection_events_stream, name='connection_events_stream'),
]
