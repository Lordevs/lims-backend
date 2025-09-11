from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # CRUD operations
    path('', views.client_list, name='client_list'),                    # GET: List all, POST: Create new
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.client_search, name='client_search'),         # GET: Search clients
    path('stats/', views.client_stats, name='client_stats'),           # GET: Client statistics
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:client_id>/', views.client_detail, name='client_detail'), # GET: Detail, PUT: Update, DELETE: Delete
]