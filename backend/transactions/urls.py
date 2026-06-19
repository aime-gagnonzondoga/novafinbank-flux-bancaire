from django.urls import path

from .views import (
    DepotView,
    RetraitView,
    HistoriqueView,
    ListeToutesTransactionsView,
)

app_name = 'transactions'

urlpatterns = [

    # ── Effectuer un dépôt ──
    # POST /api/transactions/depot/
    path('depot/', DepotView.as_view(), name='depot'),

    # ── Effectuer un retrait ──
    # POST /api/transactions/retrait/
    path('retrait/', RetraitView.as_view(), name='retrait'),

    # ── Historique des transactions d'un compte ──
    # GET /api/transactions/historique/?compte_id=1&date_debut=2026-01-01
    path('historique/', HistoriqueView.as_view(), name='historique'),

    # ── Toutes les transactions — Admin uniquement ──
    # GET /api/transactions/toutes/
    path('toutes/', ListeToutesTransactionsView.as_view(), name='toutes-transactions'),
]