from django.urls import path
from . import views

app_name = 'certificateitems'

urlpatterns = [
    # CRUD operations
    path('', views.certificate_item_list, name='certificate_item_list'),                          # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.certificate_item_search, name='certificate_item_search'),               # GET: Search certificate items
    path('stats/', views.certificate_item_stats, name='certificate_item_stats'),                 # GET: Certificate item statistics
    path('certificate/<str:certificate_id>/', views.certificate_item_by_certificate, name='certificate_item_by_certificate'), # GET: Items by certificate
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:item_id>/', views.certificate_item_detail, name='certificate_item_detail'),       # GET: Detail, PUT: Update, DELETE: Delete
]