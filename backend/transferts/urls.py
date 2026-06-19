from django.urls import path

from .views import (
    TransfertView,
    DetailTransfertView,
    ListeTousTransfertsView,
)

app_name = 'transferts'

urlpatterns = [

    # GET  /api/transferts/ → liste des transferts du client
    # POST /api/transferts/ → effectuer un transfert
    path('', TransfertView.as_view(), name='transferts'),

    # GET /api/transferts/tous/ → tous les transferts (Admin)
    path('tous/', ListeTousTransfertsView.as_view(), name='tous-transferts'),

    # GET /api/transferts/1/ → détail d'un transfert
    path('<int:pk>/', DetailTransfertView.as_view(), name='detail-transfert'),
]