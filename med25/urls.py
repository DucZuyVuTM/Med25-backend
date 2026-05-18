"""
URL configuration for med25 project.

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
from accounts.views import RegistrationView, HomeView

import med25.admin_widgets

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth built-in (login, logout, password change/reset)
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/', RegistrationView.as_view(), name='registration'),

    # Homepage
    path('', HomeView.as_view(), name='home'),

    # Apps
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('documents/', include('documents.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('messaging/', include('messaging.urls')),
    path('equipment/', include('equipment.urls')),
]
