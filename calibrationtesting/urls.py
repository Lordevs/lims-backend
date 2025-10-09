from django.urls import path
from . import views

app_name = 'calibrationtesting'

urlpatterns = [
    # Calibration Test CRUD endpoints
    path('', views.calibration_test_list, name='calibration_test_list'),
  
    # Calibration Test utility endpoints
    path('search/', views.calibration_test_search, name='calibration_test_search'),
     path('stats/', views.calibration_test_stats, name='calibration_test_stats'),
    path('overdue/', views.calibration_test_overdue, name='calibration_test_overdue'),
    path('due-soon/', views.calibration_test_due_soon, name='calibration_test_due_soon'),
      path('<str:test_id>/', views.calibration_test_detail, name='calibration_test_detail'),
   
]
