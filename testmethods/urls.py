from django.urls import path
from . import views

app_name = 'testmethods'

urlpatterns = [
    # CRUD operations
    path('', views.test_method_list, name='test_method_list'),                        # GET: List all, POST: Create new
    
    # Additional endpoints - these must come BEFORE the detail endpoint
    path('search/', views.test_method_search, name='test_method_search'),             # GET: Search test methods
    path('stats/', views.test_method_stats, name='test_method_stats'),               # GET: Test method statistics
    
    # Detail endpoint - this must come LAST to avoid conflicts
    path('<str:test_method_id>/', views.test_method_detail, name='test_method_detail'), # GET: Detail, PUT: Update, DELETE: Delete
]