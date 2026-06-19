# APIView permet de créer des vues basées sur des classes
from rest_framework.views import APIView

# Response permet de retourner des réponses JSON
from rest_framework.response import Response

# status contient les codes HTTP
from rest_framework import status

# IsAuthenticated — session active requise (RG0)
from rest_framework.permissions import IsAuthenticated

# On importe les modèles
from .models import ActionAgent, LogSecurite, Parametre

# On importe les serializers
from .serializers import (
    ActionAgentSerializer,
    LogSecuriteSerializer,
    ParametreSerializer,
    ModifierParametreSerializer,
)

# EstAgent supprimé — non utilisé dans ce fichier
from utilisateurs.permissions import EstAdministrateur


# ============================================
# VUE LISTE ACTIONS AGENT
# ============================================

# ListeActionsAgentView retourne toutes les actions de l'agent connecté
# IsAuthenticated — RG0
# Conforme à RG2 — traçabilité des actions agent
class ListeActionsAgentView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourner toutes les actions de l'agent connecté"""

        # Vérifier que l'utilisateur connecté est bien un agent
        # On vérifie le rôle d'abord — plus propre que except Exception
        if request.user.role != 'AGENT':
            return Response(
                {'error': 'Accès refusé. Réservé aux agents.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Récupérer le profil agent via la relation OneToOne
        # AttributeError — si la relation agent n'existe pas
        try:
            agent = request.user.agent
        except AttributeError:
            return Response(
                {'error': 'Profil agent introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Récupérer toutes les actions de cet agent
        # select_related → évite requêtes supplémentaires
        # order_by('-date') → plus récent en premier
        actions = ActionAgent.objects.select_related(
            'agent', 'compte'
        ).filter(agent=agent).order_by('-date')

        serializer = ActionAgentSerializer(actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# VUE LISTE LOGS DE SÉCURITÉ
# ============================================

# ListeLogsSecuriteView retourne tous les logs — Admin uniquement
# EstAdministrateur — RG9
class ListeLogsSecuriteView(APIView):

    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner tous les logs de sécurité — réservé à l'Administrateur"""

        logs = LogSecurite.objects.select_related(
            'utilisateur'
        ).all().order_by('-date_heure')

        serializer = LogSecuriteSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# VUE LISTE PARAMÈTRES
# ============================================

# ListeParametresView retourne tous les paramètres globaux
# EstAdministrateur — RG9
class ListeParametresView(APIView):

    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner tous les paramètres globaux"""

        parametres = Parametre.objects.all().order_by('cle')
        serializer = ParametreSerializer(parametres, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# VUE MODIFIER PARAMÈTRE
# ============================================

# ModifierParametreView gère la modification d'un paramètre
# EstAdministrateur — RG9
class ModifierParametreView(APIView):

    permission_classes = [EstAdministrateur]

    def patch(self, request, cle):
        """Modifier la valeur d'un paramètre global"""

        # Récupérer le paramètre par sa clé unique
        try:
            parametre = Parametre.objects.get(cle=cle)
        except Parametre.DoesNotExist:
            return Response(
                {'error': f"Paramètre '{cle}' introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Valider la nouvelle valeur
        # La clé est passée dans le contexte pour validation spécifique
        serializer = ModifierParametreSerializer(
            data=request.data,
            context={'cle': cle}
        )

        if serializer.is_valid(raise_exception=True):
            parametre.valeur = serializer.validated_data['valeur']
            parametre.save()

            return Response(
                {
                    'message'   : f"Paramètre '{cle}' mis à jour avec succès.",
                    'parametre' : ParametreSerializer(parametre).data,
                },
                status=status.HTTP_200_OK
            )


# ============================================
# VUE LISTE TOUTES LES ACTIONS AGENTS
# ============================================

# ListeToutesActionsView — Admin uniquement — RG9
class ListeToutesActionsView(APIView):

    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner toutes les actions agents — réservé à l'Administrateur"""

        actions = ActionAgent.objects.select_related(
            'agent', 'compte'
        ).all().order_by('-date')

        serializer = ActionAgentSerializer(actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)