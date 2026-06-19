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

# admin permet d'accéder au panel Django Admin
from django.contrib import admin

# path et include permettent de définir et déléguer les routes
from django.urls import path, include

# JWT — vues d'authentification fournies par simplejwt
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# settings et static pour servir les fichiers media (photos de profil)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # ── Panel Django Admin ──
    path('admin/', admin.site.urls),

    # ── Authentification JWT ──
    # POST /api/auth/login/   → obtenir access + refresh token
    # POST /api/auth/refresh/ → renouveler le access token
    path('api/auth/login/',   TokenObtainPairView.as_view(), name='token-login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(),    name='token-refresh'),

    # ── Apps NovaFinBank ──
    # include() délègue vers les urls.py de chaque app
    path('api/', include('utilisateurs.urls')),
    path('api/comptes/',      include('comptes.urls')),
    path('api/transferts/',   include('transferts.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/rapports/',     include('rapports.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# static() → sert les fichiers media (photos de profil) en développement