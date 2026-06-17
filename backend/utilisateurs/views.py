# APIView permet de créer des vues basées sur des classes
from rest_framework.views import APIView

# Response permet de retourner des réponses JSON
from rest_framework.response import Response

# status contient les codes HTTP
from rest_framework import status

# permissions permet de contrôler l'accès aux vues
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission

# On importe les modèles
from .models import Utilisateur, Client, Agent

# On importe les serializers — tous en haut du fichier
from .serializers import (
    ClientInscriptionSerializer,
    ClientSerializer,
    AgentSerializer,
    AgentCreationSerializer,
    UtilisateurSerializer,
)


# ============================================
# PERMISSION PERSONNALISÉE ADMINISTRATEUR
# ============================================

# EstAdministrateur vérifie que l'utilisateur connecté est un Administrateur
# Utilisée dans CreerAgentView et ListeUtilisateursView (RG9)
class EstAdministrateur(BasePermission):
    """Permission réservée aux Administrateurs — RG9"""

    def has_permission(self, request, view):
        # L'utilisateur doit être connecté ET avoir le rôle ADMINISTRATEUR
        return (
            request.user.is_authenticated and
            request.user.role == 'ADMINISTRATEUR'
        )


# ============================================
# VUE INSCRIPTION CLIENT
# ============================================

# InscriptionClientView gère l'inscription d'un nouveau client
# AllowAny — accessible sans authentification
# Conforme à RG1
class InscriptionClientView(APIView):

    # AllowAny — pas besoin d'être connecté pour s'inscrire
    permission_classes = [AllowAny]

    def post(self, request):
        """Créer un nouveau client"""

        serializer = ClientInscriptionSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid(raise_exception=True):
            client = serializer.save()
            return Response(
                {
                    'message' : 'Compte client créé avec succès.',
                    'client'  : ClientSerializer(client).data,
                },
                status=status.HTTP_201_CREATED
            )


# ============================================
# VUE PROFIL CLIENT
# ============================================

# ProfilClientView gère l'affichage et la modification du profil client
# IsAuthenticated — RG0
class ProfilClientView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourner le profil du client connecté"""

        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response(
                {'error': 'Profil client introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Modifier partiellement le profil du client connecté"""

        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response(
                {'error': 'Profil client introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ClientSerializer(
            client,
            data=request.data,
            partial=True
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    'message' : 'Profil mis à jour avec succès.',
                    'client'  : serializer.data,
                },
                status=status.HTTP_200_OK
            )


# ============================================
# VUE PROFIL AGENT
# ============================================

# ProfilAgentView gère l'affichage et la modification du profil agent
# IsAuthenticated — RG0
class ProfilAgentView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourner le profil de l'agent connecté"""

        try:
            agent = request.user.agent
        except Agent.DoesNotExist:
            return Response(
                {'error': 'Profil agent introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSerializer(agent)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Modifier partiellement le profil de l'agent connecté"""

        try:
            agent = request.user.agent
        except Agent.DoesNotExist:
            return Response(
                {'error': 'Profil agent introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSerializer(
            agent,
            data=request.data,
            partial=True
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    'message' : 'Profil mis à jour avec succès.',
                    'agent'   : serializer.data,
                },
                status=status.HTTP_200_OK
            )


# ============================================
# VUE CRÉATION AGENT
# ============================================

# CreerAgentView gère la création d'un nouvel agent
# EstAdministrateur — RG9
class CreerAgentView(APIView):

    # EstAdministrateur remplace la vérification manuelle du rôle
    permission_classes = [EstAdministrateur]

    def post(self, request):
        """Créer un nouvel agent — réservé à l'Administrateur"""

        serializer = AgentCreationSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            agent = serializer.save()
            return Response(
                {
                    'message' : 'Agent créé avec succès.',
                    'agent'   : AgentSerializer(agent).data,
                },
                status=status.HTTP_201_CREATED
            )


# ============================================
# VUE LISTE UTILISATEURS
# ============================================

# ListeUtilisateursView gère la liste et la modification des utilisateurs
# EstAdministrateur — RG9
class ListeUtilisateursView(APIView):

    # EstAdministrateur remplace la vérification manuelle du rôle
    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner la liste de tous les utilisateurs"""

        utilisateurs = Utilisateur.objects.all().order_by('-date_creation')
        serializer   = UtilisateurSerializer(utilisateurs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Activer ou désactiver un utilisateur"""

        # Récupérer l'utilisateur à modifier
        try:
            utilisateur = Utilisateur.objects.get(pk=pk)
        except Utilisateur.DoesNotExist:
            return Response(
                {'error': 'Utilisateur introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Récupérer is_active depuis la requête
        is_active = request.data.get('is_active')

        if is_active is None:
            return Response(
                {'error': 'Le champ is_active est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convertir string en boolean si nécessaire
        # React peut envoyer "true" ou "false" comme string
        if isinstance(is_active, str):
            is_active = is_active.lower() == 'true'

        utilisateur.is_active = is_active
        utilisateur.save()

        return Response(
            {
                'message'     : f"Utilisateur {'activé' if is_active else 'désactivé'} avec succès.",
                'utilisateur' : {
                    'id'        : utilisateur.id,
                    'email'     : utilisateur.email,
                    'is_active' : utilisateur.is_active,
                },
            },
            status=status.HTTP_200_OK
        )