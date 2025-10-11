from django.urls import path
from . import views

urlpatterns = [
    # Motor management endpoints
    path('api/motors/add/<int:motor_number>/<path:device>/', views.add_motor, name='add_motor'),
    path('api/motors/', views.get_motors, name='get_motors'),
    path('api/motors/remove/<int:motor_number>/', views.remove_motor, name='remove_motor'),

    # Available ports endpoint
    path('api/available_ports/', views.get_available_ports, name='get_available_ports'),
]
