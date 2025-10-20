from django.urls import path
from . import views

app_name = 'weldercertificates'

urlpatterns = [
    # Welder certificate CRUD endpoints
    path('', views.welder_certificate_list, name='welder_certificate_list'),                    # GET/POST: List/Create certificates
    path('search/', views.welder_certificate_search, name='welder_certificate_search'),         # GET: Search certificates
    path('stats/', views.welder_certificate_stats, name='welder_certificate_stats'),           # GET: Certificate statistics
    path('by-card/<str:welder_card_id>/', views.welder_certificate_by_card, name='welder_certificate_by_card'), # GET: Certificates by card
    path('<str:object_id>/', views.welder_certificate_detail, name='welder_certificate_detail'), # GET/PUT/DELETE: Certificate details
]
