from django.urls import path
from . import views

app_name = 'weldercards'

urlpatterns = [
    # Welder card CRUD endpoints
    path('', views.welder_card_list, name='welder_card_list'),                    # GET/POST: List/Create welder cards
    path('search/', views.welder_card_search, name='welder_card_search'),         # GET: Search welder cards
    path('stats/', views.welder_card_stats, name='welder_card_stats'),           # GET: Welder card statistics
    path('<str:object_id>/', views.welder_card_detail, name='welder_card_detail'), # GET/PUT/DELETE: Welder card details
    path('by-welder/<str:welder_id>/', views.welder_card_by_welder, name='welder_card_by_welder'), # GET: Cards by welder
]
