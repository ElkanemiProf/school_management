"""
URL configuration for school_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf.urls import handler403
from main.views import permission_denied_view  # Import your custom 403 view
handler403 = permission_denied_view
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', include('main.urls')),
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
