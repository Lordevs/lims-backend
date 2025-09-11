from django.urls import path
from . import views

app_name = 'samplelots'

urlpatterns = [
    # CRUD operations
    path('', views.sample_lot_list, name='sample_lot_list'),                          # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.sample_lot_search, name='sample_lot_search'),               # GET: Search sample lots
    path('stats/', views.sample_lot_stats, name='sample_lot_stats'),                 # GET: Sample lot statistics
    path('job/<str:job_id>/', views.sample_lot_by_job, name='sample_lot_by_job'),    # GET: Sample lots by job
    # path('job/<str:job_id>/delete/', views.delete_sample_lots_by_job, name='delete_sample_lots_by_job'), # DELETE: Cascade delete by job
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:item_no>/', views.sample_lot_detail, name='sample_lot_detail'),       # GET: Detail, PUT: Update, DELETE: Delete
]