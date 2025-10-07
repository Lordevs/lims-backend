"""
URL configuration for lims_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/clients/', include('clients.urls')),
    path('api/jobs/', include('samplejobs.urls')),
    path('api/sample-lots/', include('samplelots.urls')),
    path('api/test-methods/', include('testmethods.urls')),
    path('api/specimens/', include('specimens.urls')),
    path('api/sample-preparations/', include('samplepreperation.urls')),
    path('api/certificates/', include('certificates.urls')),
    path('api/certificate-items/', include('certificateitems.urls')),
]
