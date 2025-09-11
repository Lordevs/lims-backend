from django.urls import path
from . import views

app_name = 'specimens'

urlpatterns = [
    # CRUD operations
    path('', views.specimen_list, name='specimen_list'),                          # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.specimen_search, name='specimen_search'),               # GET: Search specimens
    path('stats/', views.specimen_stats, name='specimen_stats'),                 # GET: Specimen statistics
    path('bulk-delete/', views.bulk_delete_specimens, name='bulk_delete_specimens'), # DELETE: Bulk delete specimens
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:specimen_id>/', views.specimen_detail, name='specimen_detail'),   # GET: Detail, PUT: Update, DELETE: Delete
]