from django.urls import path
from . import views

app_name = 'samplepreperation'

urlpatterns = [
    # CRUD operations
    path('', views.sample_preparation_list, name='sample_preparation_list'),                          # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.sample_preparation_search, name='sample_preparation_search'),               # GET: Search sample preparations
    path('stats/', views.sample_preparation_stats, name='sample_preparation_stats'),                 # GET: Sample preparation statistics
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:request_no>/', views.sample_preparation_detail, name='sample_preparation_detail'),    # GET: Detail, PUT: Update, DELETE: Delete
]