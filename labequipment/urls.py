from django.urls import path
from . import views

app_name = 'labequipment'

urlpatterns = [
    # Equipment utility endpoints (must come before detail endpoint)
    path('search/', views.equipment_search, name='equipment_search'),
    path('stats/', views.equipment_stats, name='equipment_stats'),
    path('verification-due/', views.equipment_verification_due, name='equipment_verification_due'),
    
    # Equipment CRUD endpoints
    path('', views.equipment_list, name='equipment_list'),
    path('<str:equipment_id>/', views.equipment_detail, name='equipment_detail'),
]
    