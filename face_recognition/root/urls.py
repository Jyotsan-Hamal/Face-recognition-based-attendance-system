"""
URL configuration for face_recognition project.

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
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.landing_page, name='landing_page'),
    path('dashboard', views.dashboard_view, name='dashboard'),
    path("logout",views.user_logout,name='logout'),
    path("dashboard/classroom",views.classroom,name='classroom'),

    path('dashboard/class<int:class_number>', views.class_details, name='class_details'),
    
    path('dashboard/add_student/<int:class_number>/', views.add_student, name='add_student'),
        
]
