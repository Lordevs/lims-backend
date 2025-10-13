from django.urls import path
from . import views

app_name = 'testingreports'

urlpatterns = [
    # Testing report CRUD endpoints
    path('', views.testing_report_list, name='testing_report_list'),                    # GET/POST: List/Create testing reports
    path('search/', views.testing_report_search, name='testing_report_search'),         # GET: Search testing reports
    path('stats/', views.testing_report_stats, name='testing_report_stats'),           # GET: Testing report statistics
    path('<str:object_id>/', views.testing_report_detail, name='testing_report_detail'), # GET/PUT/DELETE: Testing report details
    path('by-welder/<str:welder_id>/', views.testing_report_by_welder, name='testing_report_by_welder'), # GET: Reports by welder
]
