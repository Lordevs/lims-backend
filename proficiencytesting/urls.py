from django.urls import path
from . import views

app_name = 'proficiencytesting'

urlpatterns = [
    # Proficiency Test CRUD endpoints
    path('', views.proficiency_test_list, name='proficiency_test_list'),
    path('<str:test_id>/', views.proficiency_test_detail, name='proficiency_test_detail'),
    
    # Proficiency Test utility endpoints
    path('search/', views.proficiency_test_search, name='proficiency_test_search'),
    path('stats/', views.proficiency_test_stats, name='proficiency_test_stats'),
    path('overdue/', views.proficiency_test_overdue, name='proficiency_test_overdue'),
]
