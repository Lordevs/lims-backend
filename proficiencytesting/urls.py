from django.urls import path
from . import views

app_name = 'proficiencytesting'

urlpatterns = [
    # Proficiency Test CRUD endpoints
    path('', views.proficiency_test_list, name='proficiency_test_list'),
    
    
    # Proficiency Test utility endpoints
    path('search/', views.proficiency_test_search, name='proficiency_test_search'),
    path('<str:test_id>/', views.proficiency_test_detail, name='proficiency_test_detail'),
]
