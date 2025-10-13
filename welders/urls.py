from django.urls import path
from . import views

app_name = 'welders'

urlpatterns = [
    # Welder CRUD endpoints
    path('', views.welder_list, name='welder_list'),                    # GET/POST: List/Create welders
    path('search/', views.welder_search, name='welder_search'),         # GET: Search welders
    path('stats/', views.welder_stats, name='welder_stats'),            # GET: Welder statistics
    path('<str:object_id>/', views.welder_detail, name='welder_detail'), # GET/PUT/DELETE: Welder details
    path('<str:object_id>/image/', views.welder_image_management, name='welder_image_management'), # POST/DELETE: Image management
]
