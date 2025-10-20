from django.urls import path
from . import views

app_name = 'pqrs'

urlpatterns = [
    # PQR CRUD endpoints
    path('', views.pqr_list, name='pqr_list'),                    # GET/POST: List/Create PQRs
    path('search/', views.pqr_search, name='pqr_search'),         # GET: Search PQRs
    path('stats/', views.pqr_stats, name='pqr_stats'),           # GET: PQR statistics
    path('<str:object_id>/', views.pqr_detail, name='pqr_detail'), # GET/PUT/DELETE: PQR details
    path('by-welder/<str:welder_id>/', views.pqr_by_welder, name='pqr_by_welder'), # GET: PQRs by welder
]
