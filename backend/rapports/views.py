from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import ActionAgent, LogSecurite, Parametre
from .serializers import (
    ActionAgentSerializer,
    LogSecuriteSerializer,
    ParametreSerializer,
    ModifierParametreSerializer,
)
from utilisateurs.permissions import EstAdministrateur, EstAgent


# ============================================
# VUE LISTE ACTIONS AGENT
# ============================================

# ListeActionsAgentView retourne toutes les actions d'un agent
# RG2 — traçabilité
class ListeActionsAgentView(APIView):

    # IsAuthenticated — session active requise (RG0)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourner toutes les actions de l'agent connecté"""

        # Vérifier que l'utilisateur est un agent
        try:
            agent = request.user.agent
        except Exception:
            return Response(
                {'error': 'Profil agent introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Récupérer toutes les actions de cet agent
        # select_related → évite requêtes supplémentaires
        actions = ActionAgent.objects.select_related(
            'agent', 'compte'
        ).filter(agent=agent).order_by('-date')

        serializer = ActionAgentSerializer(actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# VUE LISTE TOUS LES LOGS DE SÉCURITÉ
# ============================================

# ListeLogsSecuriteView retourne tous les logs — Admin uniquement
# RG9 — l'administrateur peut consulter les logs de sécurité
class ListeLogsSecuriteView(APIView):

    # EstAdministrateur — RG9
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

# ListeParametresView retourne tous les paramètres
# EstAdministrateur — RG9
class ListeParametresView(APIView):

    # EstAdministrateur — RG9
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

    # EstAdministrateur — RG9
    permission_classes = [EstAdministrateur]

    def patch(self, request, cle):
        """Modifier la valeur d'un paramètre global"""

        # Récupérer le paramètre par sa clé
        try:
            parametre = Parametre.objects.get(cle=cle)
        except Parametre.DoesNotExist:
            return Response(
                {'error': f"Paramètre '{cle}' introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Valider la nouvelle valeur
        # On passe la clé dans le contexte pour validation spécifique
        serializer = ModifierParametreSerializer(
            data=request.data,
            context={'cle': cle}
        )

        if serializer.is_valid(raise_exception=True):

            # Mettre à jour la valeur
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

# ListeToutesActionsView retourne toutes les actions — Admin uniquement
# RG9
class ListeToutesActionsView(APIView):

    # EstAdministrateur — RG9
    permission_classes = [EstAdministrateur]

    def get(self, request):
        """Retourner toutes les actions agents — réservé à l'Administrateur"""

        actions = ActionAgent.objects.select_related(
            'agent', 'compte'
        ).all().order_by('-date')

        serializer = ActionAgentSerializer(actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)