from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login, name='login'),                    # POST: User login
    path('register/', views.register, name='register'),           # POST: User registration
    path('refresh/', views.refresh_token, name='refresh_token'),  # POST: Refresh access token
    path('logout/', views.logout, name='logout'),                 # POST: User logout
    path('verify/', views.verify_token, name='verify_token'),     # GET: Verify access token
    
    # User management endpoints
    path('users/', views.user_list, name='user_list'),            # GET: List all users (Admin only)
    path('users/<str:user_id>/', views.user_detail, name='user_detail'),  # GET: Get user details
]
