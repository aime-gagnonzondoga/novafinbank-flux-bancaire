# APIView permet de créer des vues basées sur des classes
from rest_framework.views import APIView

# Response permet de retourner des réponses JSON
from rest_framework.response import Response

# status contient les codes HTTP
from rest_framework import status

# IsAuthenticated — session active requise (RG0)
from rest_framework.permissions import IsAuthenticated

# uuid pour générer le numéro de compte automatiquement
import uuid

# On importe le modèle Compte
from .models import Compte

# On importe les serializers
from .serializers import (
    CompteSerializer,
    OuvrirCompteSerializer,
    SuspendreCompteSerializer,
    ReactiverCompteSerializer,
)

# On importe Client — Agent accédé via request.user.agent
from utilisateurs.models import Client

# On importe Transaction pour le dépôt initial (RG3)
from transactions.models import Transaction

# On importe ActionAgent pour la traçabilité (RG2)
from rapports.models import ActionAgent

# On importe les permissions depuis le fichier dédié
# Evite les imports circulaires
from utilisateurs.permissions import EstAdministrateur, EstAgent


# ============================================
# VUE LISTE COMPTES CLIENT
# ============================================

# ListeComptesClientView retourne tous les comptes du client connecté
# IsAuthenticated — RG0
class ListeComptesClientView(APIView):

    # IsAuthenticated — session active requise (RG0)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourner tous les comptes du client connecté"""

        # Vérifier que l'utilisateur connecté est bien un client
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response(
                {'error': 'Profil client introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # select_related évite les requêtes supplémentaires
        comptes    = Compte.objects.select_related('client', 'agent').filter(client=client)
        serializer = CompteSerializer(comptes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# VUE DÉTAIL COMPTE
# ============================================

# DetailCompteView retourne le détail d'un compte spécifique
# IsAuthenticated — RG0
class DetailCompteView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Retourner le détail d'un compte"""

        try:
            compte = Compte.objects.select_related('client', 'agent').get(pk=pk)
        except Compte.DoesNotExist:
            return Response(
                {'error': 'Compte introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Un client ne peut voir que ses propres comptes
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

        serializer = CompteSerializer(compte)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# VUE OUVRIR COMPTE
# ============================================

# OuvrirCompteView gère l'ouverture d'un nouveau compte
# EstAgent — RG2, RG3
class OuvrirCompteView(APIView):

    permission_classes = [EstAgent]

    def post(self, request):
        """Ouvrir un nouveau compte pour un client"""

        serializer = OuvrirCompteSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data

            # Récupérer le client et l'agent connecté
            client = Client.objects.get(id=validated_data['client_id'])
            agent  = request.user.agent

            # Générer le numéro de compte — Format : CPT-XXXXXXXXXX
            # uuid importé en haut du fichier
            numero = f"CPT-{uuid.uuid4().hex[:10].upper()}"

            # Créer le compte — RG3
            compte = Compte.objects.create(
                numero = numero,
                type   = validated_data['type'],
                statut = 'ACTIF',
                solde  = validated_data['depot_initial'],
                client = client,
                agent  = agent,
            )

            # Créer la transaction dépôt initial — RG3
            Transaction.objects.create(
                type    = 'DEPOT',
                montant = validated_data['depot_initial'],
                frais   = 0,
                statut  = 'SUCCES',
                compte  = compte,
            )

            # Tracer l'action de l'agent — RG2
            ActionAgent.objects.create(
                type_action = 'OUVERTURE_COMPTE',
                description = f"Ouverture compte {compte.numero} pour {client.nom} {client.prenom}",
                agent       = agent,
                compte      = compte,
            )

            return Response(
                {
                    'message' : 'Compte ouvert avec succès.',
                    'compte'  : CompteSerializer(compte).data,
                },
                status=status.HTTP_201_CREATED
            )


# ============================================
# VUE SUSPENDRE COMPTE
# ============================================

# SuspendreCompteView gère la suspension d'un compte
# EstAgent — RG2
class SuspendreCompteView(APIView):

    permission_classes = [EstAgent]

    def patch(self, request, pk):
        """Suspendre un compte"""

        try:
            compte = Compte.objects.get(pk=pk)
        except Compte.DoesNotExist:
            return Response(
                {'error': 'Compte introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SuspendreCompteSerializer(
            data=request.data,
            context={'compte': compte}
        )

        if serializer.is_valid(raise_exception=True):

            # Suspendre le compte — RG3
            compte.statut = 'SUSPENDU'
            compte.save()

            # Tracer l'action — RG2
            agent = request.user.agent
            ActionAgent.objects.create(
                type_action = 'SUSPENSION_COMPTE',
                description = serializer.validated_data.get('motif', ''),
                agent       = agent,
                compte      = compte,
            )

            return Response(
                {
                    'message' : 'Compte suspendu avec succès.',
                    'compte'  : CompteSerializer(compte).data,
                },
                status=status.HTTP_200_OK
            )


# ============================================
# VUE RÉACTIVER COMPTE
# ============================================

# ReactiverCompteView gère la réactivation d'un compte suspendu
# EstAgent — RG2
class ReactiverCompteView(APIView):

    permission_classes = [EstAgent]

    def patch(self, request, pk):
        """Réactiver un compte suspendu"""

        try:
            compte = Compte.objects.get(pk=pk)
        except Compte.DoesNotExist:
            return Response(
                {'error': 'Compte introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReactiverCompteSerializer(
            data=request.data,
            context={'compte': compte}
        )

        if serializer.is_valid(raise_exception=True):

            # Réactiver le compte — RG3
            compte.statut = 'ACTIF'
            compte.save()

            # Tracer l'action — RG2
            agent = request.user.agent
            ActionAgent.objects.create(
                type_action = 'REACTIVATION_COMPTE',
                description = serializer.validated_data.get('motif', ''),
                agent       = agent,
                compte      = compte,
            )

            return Response(
                {
                    'message' : 'Compte réactivé avec succès.',
                    'compte'  : CompteSerializer(compte).data,
                },
                status=status.HTTP_200_OK
            )


# ============================================
# VUE LISTE TOUS LES COMPTES
# ============================================

# ListeTousComptesView — Admin uniquement — RG9
class ListeTousComptesView(APIView):

    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner tous les comptes — réservé à l'Administrateur"""

        comptes    = Compte.objects.select_related('client', 'agent').all()
        serializer = CompteSerializer(comptes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)