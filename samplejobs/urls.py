from django.urls import path
from . import views

app_name = 'samplejobs'

urlpatterns = [
    # CRUD operations
    path('', views.job_list, name='job_list'),                          # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.job_search, name='job_search'),               # GET: Search jobs
    path('stats/', views.job_stats, name='job_stats'),                 # GET: Job statistics
    path('bulk-delete/', views.bulk_delete_jobs, name='bulk_delete_jobs'), # DELETE: Bulk delete jobs
    path('client/<str:client_id>/', views.job_by_client, name='job_by_client'), # GET: Jobs by client
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:job_id>/', views.job_detail, name='job_detail'),         # GET: Detail, PUT: Update, DELETE: Delete
]