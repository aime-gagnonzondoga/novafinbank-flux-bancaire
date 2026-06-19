# APIView permet de créer des vues basées sur des classes
from rest_framework.views import APIView

# Response permet de retourner des réponses JSON
from rest_framework.response import Response

# status contient les codes HTTP
from rest_framework import status

# permissions permet de contrôler l'accès aux vues
from rest_framework.permissions import IsAuthenticated, AllowAny
from utilisateurs.permissions import EstAdministrateur


# Ajouter ces imports en haut de utilisateurs/views.py
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rapports.models import LogSecurite


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
        
        
        
        
        
        
        
        
        
        
    


# ============================================
# FONCTION UTILITAIRE — RÉCUPÉRER IP
# ============================================

def get_adresse_ip(request):
    """Récupère l'adresse IP de l'utilisateur
    HTTP_X_FORWARDED_FOR → si derrière un proxy
    REMOTE_ADDR → adresse directe sinon
    """
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        # Prendre la première IP de la liste
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


# ============================================
# VUE LOGIN CLIENT
# ============================================

# LoginClientView gère la connexion d'un client
# AllowAny — accessible sans authentification
# Conforme à RG0
class LoginClientView(APIView):

    # AllowAny — pas besoin d'être connecté pour se connecter
    permission_classes = [AllowAny]

    def post(self, request):
        """Connecter un client avec email + mot_de_passe"""

        # Récupérer les données envoyées par React
        email        = request.data.get('email')
        mot_de_passe = request.data.get('mot_de_passe')

        # Récupérer l'IP pour les logs — RG9
        adresse_ip = get_adresse_ip(request)

        # Vérifier que les deux champs sont fournis
        if not email or not mot_de_passe:
            return Response(
                {'error': 'Email et mot de passe requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # authenticate() vérifie email + mot_de_passe
        # Retourne l'utilisateur si correct, None sinon
        utilisateur = authenticate(
            request,
            username=email,
            password=mot_de_passe
        )

        if utilisateur is None:
            # Connexion échouée — enregistrer le log — RG9
            LogSecurite.objects.create(
                action     = 'TENTATIVE_ECHEC',
                adresse_ip = adresse_ip,
                details    = f"Tentative échouée avec email : {email}",
                utilisateur = None,
            )
            return Response(
                {'error': 'Email ou mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Vérifier que c'est bien un CLIENT
        if utilisateur.role != 'CLIENT':
            return Response(
                {'error': 'Ce compte n\'est pas un compte client.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Vérifier que le compte est actif — RG0
        if not utilisateur.is_active:
            return Response(
                {'error': 'Ce compte est désactivé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(utilisateur)

        # Enregistrer la connexion réussie — RG9
        LogSecurite.objects.create(
            action      = 'CONNEXION',
            adresse_ip  = adresse_ip,
            details     = f"Connexion client réussie : {email}",
            utilisateur = utilisateur,
        )

        # Récupérer le profil client
        client = utilisateur.client

        return Response(
            {
                'access'  : str(refresh.access_token),
                'refresh' : str(refresh),
                'role'    : utilisateur.role,
                'client'  : ClientSerializer(client).data,
            },
            status=status.HTTP_200_OK
        )


# ============================================
# VUE LOGIN AGENT
# ============================================

# LoginAgentView gère la connexion d'un agent
# AllowAny — accessible sans authentification
# Conforme à RG0
class LoginAgentView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        """Connecter un agent avec matricule + mot_de_passe"""

        matricule    = request.data.get('matricule')
        mot_de_passe = request.data.get('mot_de_passe')
        adresse_ip   = get_adresse_ip(request)

        if not matricule or not mot_de_passe:
            return Response(
                {'error': 'Matricule et mot de passe requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Un agent se connecte avec son matricule
        # On cherche d'abord l'agent par matricule
        # pour récupérer son email lié à Utilisateur
        try:
            from utilisateurs.models import Agent
            agent        = Agent.objects.select_related('utilisateur').get(
                matricule=matricule
            )
            utilisateur  = agent.utilisateur
        except Agent.DoesNotExist:
            # Matricule inexistant — log tentative échouée
            LogSecurite.objects.create(
                action      = 'TENTATIVE_ECHEC',
                adresse_ip  = adresse_ip,
                details     = f"Tentative échouée avec matricule : {matricule}",
                utilisateur = None,
            )
            return Response(
                {'error': 'Matricule ou mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Vérifier le mot de passe via authenticate
        utilisateur_auth = authenticate(
            request,
            username=utilisateur.email,
            password=mot_de_passe
        )

        if utilisateur_auth is None:
            # Mot de passe incorrect — log tentative échouée
            LogSecurite.objects.create(
                action      = 'TENTATIVE_ECHEC',
                adresse_ip  = adresse_ip,
                details     = f"Mot de passe incorrect pour matricule : {matricule}",
                utilisateur = utilisateur,
            )
            return Response(
                {'error': 'Matricule ou mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Vérifier que le compte est actif — RG0
        if not utilisateur.is_active:
            return Response(
                {'error': 'Ce compte est désactivé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(utilisateur)

        # Enregistrer la connexion réussie — RG9
        LogSecurite.objects.create(
            action      = 'CONNEXION',
            adresse_ip  = adresse_ip,
            details     = f"Connexion agent réussie : {matricule}",
            utilisateur = utilisateur,
        )

        return Response(
            {
                'access'  : str(refresh.access_token),
                'refresh' : str(refresh),
                'role'    : utilisateur.role,
                'agent'   : AgentSerializer(agent).data,
            },
            status=status.HTTP_200_OK
        )


# ============================================
# VUE DÉCONNEXION
# ============================================

# LogoutView gère la déconnexion — invalide le refresh token
# IsAuthenticated — RG0
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Déconnecter l'utilisateur en invalidant son refresh token"""

        adresse_ip = get_adresse_ip(request)

        try:
            # Récupérer le refresh token depuis la requête
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token requis.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Blacklister le refresh token — il ne pourra plus être utilisé
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Enregistrer la déconnexion — RG9
            LogSecurite.objects.create(
                action      = 'DECONNEXION',
                adresse_ip  = adresse_ip,
                details     = f"Déconnexion : {request.user.email}",
                utilisateur = request.user,
            )

            return Response(
                {'message': 'Déconnexion réussie.'},
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {'error': 'Token invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )