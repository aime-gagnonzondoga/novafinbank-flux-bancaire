from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction

from .models import Transaction
from .serializers import (
    TransactionSerializer,
    DepotSerializer,
    RetraitSerializer,
    HistoriqueSerializer,
)
from comptes.models import Compte
from utilisateurs.models import Client
from utilisateurs.permissions import EstAdministrateur


# ============================================
# VUE DÉPÔT
# ============================================

# DepotView gère la création d'un dépôt
# IsAuthenticated — RG0
# Conforme à RG4
class DepotView(APIView):

    # IsAuthenticated — tout utilisateur connecté peut déposer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Effectuer un dépôt sur un compte"""

        serializer = DepotSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            compte         = validated_data['compte']
            montant        = validated_data['montant']

            try:
                # transaction.atomic() — tout ou rien
                # Si une opération échoue → tout est annulé
                with db_transaction.atomic():

                    # RG4 — mettre à jour le solde immédiatement
                    compte.solde += montant
                    compte.save()

                    # RG4 — créer la transaction DEPOT
                    # RG7 — référence unique auto-générée par le modèle
                    nouvelle_transaction = Transaction.objects.create(
                        type    = 'DEPOT',
                        montant = montant,
                        frais   = 0,        # RG4 — dépôts gratuits
                        statut  = 'SUCCES',
                        compte  = compte,
                    )

            except Exception:
                # RG7 — transaction échouée ne modifie pas le solde
                # On crée une transaction ECHEC sans modifier le solde
                nouvelle_transaction = Transaction.objects.create(
                    type    = 'DEPOT',
                    montant = montant,
                    frais   = 0,
                    statut  = 'ECHEC',
                    compte  = compte,
                )
                return Response(
                    {
                        'error'       : 'Dépôt échoué. Solde inchangé.',
                        'transaction' : TransactionSerializer(nouvelle_transaction).data,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {
                    'message'       : 'Dépôt effectué avec succès.',
                    'transaction'   : TransactionSerializer(nouvelle_transaction).data,
                    'nouveau_solde' : str(compte.solde),
                },
                status=status.HTTP_201_CREATED
            )


# ============================================
# VUE RETRAIT
# ============================================

# RetraitView gère la création d'un retrait
# IsAuthenticated — RG0
# Conforme à RG5
class RetraitView(APIView):

    # IsAuthenticated — tout utilisateur connecté peut retirer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Effectuer un retrait sur un compte"""

        # Toutes les règles RG5 sont validées dans le serializer
        serializer = RetraitSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            compte         = validated_data['compte']
            montant        = validated_data['montant']

            try:
                with db_transaction.atomic():

                    # RG5 — mettre à jour le solde
                    compte.solde -= montant
                    compte.save()

                    # RG5 — créer la transaction RETRAIT
                    # RG7 — référence unique auto-générée
                    nouvelle_transaction = Transaction.objects.create(
                        type    = 'RETRAIT',
                        montant = montant,
                        frais   = 0,        # RG5 — retraits gratuits
                        statut  = 'SUCCES',
                        compte  = compte,
                    )

            except Exception:
                # RG7 — transaction échouée ne modifie pas le solde
                nouvelle_transaction = Transaction.objects.create(
                    type    = 'RETRAIT',
                    montant = montant,
                    frais   = 0,
                    statut  = 'ECHEC',
                    compte  = compte,
                )
                return Response(
                    {
                        'error'       : 'Retrait échoué. Solde inchangé.',
                        'transaction' : TransactionSerializer(nouvelle_transaction).data,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {
                    'message'       : 'Retrait effectué avec succès.',
                    'transaction'   : TransactionSerializer(nouvelle_transaction).data,
                    'nouveau_solde' : str(compte.solde),
                },
                status=status.HTTP_201_CREATED
            )


# ============================================
# VUE HISTORIQUE
# ============================================

# HistoriqueView retourne l'historique des transactions d'un compte
# IsAuthenticated — RG0
# Conforme à RG8
class HistoriqueView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourner l'historique des transactions d'un compte"""

        # query_params → paramètres GET dans l'URL
        # ex: /api/transactions/historique/?compte_id=1&date_debut=2026-01-01
        historique_serializer = HistoriqueSerializer(data=request.query_params)

        if historique_serializer.is_valid(raise_exception=True):
            validated_data = historique_serializer.validated_data

            compte_id  = validated_data['compte_id']
            date_debut = validated_data.get('date_debut')
            date_fin   = validated_data.get('date_fin')
            ordre      = validated_data.get('ordre', 'antéchronologique')

            # Récupérer le compte
            try:
                compte = Compte.objects.get(id=compte_id)
            except Compte.DoesNotExist:
                return Response(
                    {'error': 'Compte introuvable.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Un client ne peut voir que ses propres comptes — RG0
            if request.user.role == 'CLIENT':
                try:
                    client = request.user.client
                    if compte.client != client:
                        return Response(
                            {'error': 'Accès refusé. Ce compte ne vous appartient pas.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Client.DoesNotExist:
                    return Response(
                        {'error': 'Profil client introuvable.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # RG8 — récupérer toutes les transactions du compte
            transactions = Transaction.objects.filter(compte=compte)

            # RG8 — filtrer par période si dates fournies
            if date_debut:
                transactions = transactions.filter(date_heure__date__gte=date_debut)
            if date_fin:
                transactions = transactions.filter(date_heure__date__lte=date_fin)

            # Compter avant order_by — évite requête supplémentaire
            total = transactions.count()

            # RG8 — trier selon l'ordre demandé
            if ordre == 'chronologique':
                transactions = transactions.order_by('date_heure')
            else:
                # antéchronologique par défaut
                transactions = transactions.order_by('-date_heure')

            # Renommé en transactions_serializer pour éviter confusion
            transactions_serializer = TransactionSerializer(transactions, many=True)

            return Response(
                {
                    'compte'       : compte.numero,
                    'total'        : total,
                    'transactions' : transactions_serializer.data,
                },
                status=status.HTTP_200_OK
            )


# ============================================
# VUE LISTE TOUTES LES TRANSACTIONS
# ============================================

# ListeToutesTransactionsView — Admin uniquement — RG9
class ListeToutesTransactionsView(APIView):

    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner toutes les transactions — réservé à l'Administrateur"""

        transactions = Transaction.objects.select_related(
            'compte'
        ).all().order_by('-date_heure')

        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)