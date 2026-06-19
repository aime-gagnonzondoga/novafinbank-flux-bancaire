from django.urls import path

from .views import (
    ListeComptesClientView,
    DetailCompteView,
    OuvrirCompteView,
    SuspendreCompteView,
    ReactiverCompteView,
    ListeTousComptesView,
)

app_name = 'comptes'

urlpatterns = [

    # ── Liste comptes du client connecté ──
    # GET /api/comptes/
    path('', ListeComptesClientView.as_view(), name='liste-comptes'),

    # ── Tous les comptes — Admin uniquement ──
    # GET /api/comptes/tous/
    # IMPORTANT : 'tous/' avant '<int:pk>/'
    # sinon Django interpréterait 'tous' comme un pk
    path('tous/', ListeTousComptesView.as_view(), name='tous-comptes'),

    # ── Ouvrir un compte — Agent uniquement ──
    # POST /api/comptes/ouvrir/
    path('ouvrir/', OuvrirCompteView.as_view(), name='ouvrir-compte'),

    # ── Détail d'un compte ──
    # GET /api/comptes/1/
    path('<int:pk>/', DetailCompteView.as_view(), name='detail-compte'),

    # ── Suspendre un compte — Agent uniquement ──
    # PATCH /api/comptes/1/suspendre/
    path('<int:pk>/suspendre/', SuspendreCompteView.as_view(), name='suspendre-compte'),

    # ── Réactiver un compte — Agent uniquement ──
    # PATCH /api/comptes/1/reactiver/
    path('<int:pk>/reactiver/', ReactiverCompteView.as_view(), name='reactiver-compte'),
]