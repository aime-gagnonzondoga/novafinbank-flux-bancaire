"""
URL configuration for novafinbank project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from utilisateurs.views import LoginClientView, LoginAgentView, LogoutView

urlpatterns = [

    path('admin/', admin.site.urls),

    # Auth JWT
    path('api/auth/login/client/', LoginClientView.as_view(),  name='login-client'),
    path('api/auth/login/agent/',  LoginAgentView.as_view(),   name='login-agent'),
    path('api/auth/refresh/',      TokenRefreshView.as_view(), name='token-refresh'),
    path('api/auth/logout/',       LogoutView.as_view(),       name='logout'),

    # Apps NovaFinBank
    path('api/',              include('utilisateurs.urls')),
    path('api/comptes/',      include('comptes.urls')),
    path('api/transferts/',   include('transferts.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/rapports/',     include('rapports.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)