from django.urls import path

from .views import (
    EffectuerTransfertView,
    ListeTransfertsClientView,
    DetailTransfertView,
    ListeTousTransfertsView,
)

app_name = 'transferts'

urlpatterns = [

    # ── Liste transferts du client ET effectuer un transfert ──
    # GET  /api/transferts/ → liste des transferts du client
    # POST /api/transferts/ → effectuer un transfert
    # Django dispatch automatiquement selon la méthode HTTP
    path('', ListeTransfertsClientView.as_view(), name='liste-transferts'),

    # ── Tous les transferts — Admin uniquement ──
    # GET /api/transferts/tous/
    # IMPORTANT : 'tous/' avant '<int:pk>/' pour éviter conflit
    path('tous/', ListeTousTransfertsView.as_view(), name='tous-transferts'),

    # ── Détail d'un transfert ──
    # GET /api/transferts/1/
    path('<int:pk>/', DetailTransfertView.as_view(), name='detail-transfert'),
]