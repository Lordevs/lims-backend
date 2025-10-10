from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    # CRUD operations
    path('', views.certificate_list, name='certificate_list'),                          # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.certificate_search, name='certificate_search'),               # GET: Search certificates
    path('stats/', views.certificate_stats, name='certificate_stats'),                 # GET: Certificate statistics
    path('request/<str:request_no>/', views.certificate_by_request, name='certificate_by_request'), # GET: Certificates by request
    path('job/<str:job_oid>/', views.certificate_by_job, name='certificate_by_job'),   # GET: Certificates by job ObjectId
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:certificate_oid>/', views.certificate_detail, name='certificate_detail'), # GET: Detail, PUT: Update, DELETE: Delete
]