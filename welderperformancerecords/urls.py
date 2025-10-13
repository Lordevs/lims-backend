from django.urls import path
from . import views

app_name = 'welderperformancerecords'

urlpatterns = [
    # Welder performance record CRUD endpoints
    path('', views.welder_performance_record_list, name='welder_performance_record_list'),                    # GET/POST: List/Create performance records
    path('<str:object_id>/', views.welder_performance_record_detail, name='welder_performance_record_detail'), # GET/PUT/DELETE: Performance record details
    path('search/', views.welder_performance_record_search, name='welder_performance_record_search'),         # GET: Search performance records
    path('stats/', views.welder_performance_record_stats, name='welder_performance_record_stats'),           # GET: Performance record statistics
    path('by-card/<str:welder_card_id>/', views.welder_performance_record_by_card, name='welder_performance_record_by_card'), # GET: Performance records by card
]
