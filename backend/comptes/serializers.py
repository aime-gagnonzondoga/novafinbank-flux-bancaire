# serializers permet de convertir les objets Python en JSON et vice versa
from rest_framework import serializers

# On importe Decimal pour les calculs financiers précis
from decimal import Decimal

# On importe le modèle Compte
from .models import Compte

# On importe Client car Compte lui est lié — Agent supprimé car non utilisé
from utilisateurs.models import Client

# On importe Parametre pour récupérer les valeurs configurables (RG3)
from rapports.models import Parametre


# ============================================
# SERIALIZER COMPTE
# ============================================
class CompteSerializer(serializers.ModelSerializer):

    # Nom complet du client au lieu de son id
    client_nom      = serializers.SerializerMethodField()

    # Matricule de l'agent au lieu de son id
    agent_matricule = serializers.SerializerMethodField()

    class Meta:
        model  = Compte
        fields = [
            'id',
            'numero',
            'type',
            'statut',
            'solde',
            'date_ouverture',
            'client_nom',
            'agent_matricule',
        ]
        read_only_fields = [
            'id',
            'numero',
            'solde',
            'date_ouverture',
            'client_nom',
            'agent_matricule',
        ]

    def get_client_nom(self, obj):
        """Retourne le nom complet du client propriétaire du compte"""
        return f"{obj.client.nom} {obj.client.prenom}"

    def get_agent_matricule(self, obj):
        """Retourne le matricule de l'agent qui a ouvert le compte"""
        return obj.agent.matricule


# ============================================
# SERIALIZER OUVERTURE COMPTE
# ============================================
class OuvrirCompteSerializer(serializers.Serializer):

    # ID du client — RG1 le client doit exister avant création compte
    client_id     = serializers.IntegerField()

    # Type de compte — COURANT ou EPARGNE (RG3)
    type          = serializers.ChoiceField(choices=['COURANT', 'EPARGNE'])

    # Dépôt initial — minimum 1500 FCFA (RG3)
    depot_initial = serializers.DecimalField(max_digits=15, decimal_places=2)

    def validate_client_id(self, value):
        # RG1 — vérifier que le client existe
        if not Client.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Ce client n'existe pas."
            )
        return value

    def validate_depot_initial(self, value):
        # Vérifier d'abord que le montant est positif
        if value <= 0:
            raise serializers.ValidationError(
                "Le dépôt initial doit être strictement positif."
            )

        # RG3 — dépôt initial minimum depuis Parametre
        try:
            depot_min = Decimal(
                Parametre.objects.get(cle='DEPOT_INITIAL_MINIMUM').valeur
            )
        except Parametre.DoesNotExist:
            depot_min = Decimal('1500')

        if value < depot_min:
            raise serializers.ValidationError(
                f"Le dépôt initial minimum est de {depot_min} FCFA."
            )
        return value


# ============================================
# SERIALIZER SUSPENSION COMPTE
# ============================================
class SuspendreCompteSerializer(serializers.Serializer):

    # Motif optionnel pour la traçabilité (RG2)
    motif = serializers.CharField(
                max_length=255,
                required=False,
                allow_blank=True
            )

    def validate(self, data):
        compte = self.context.get('compte')

        # Vérifier que le compte existe
        if not compte:
            raise serializers.ValidationError("Compte introuvable.")

        # RG3 — impossible de suspendre un compte déjà suspendu
        if compte.statut == 'SUSPENDU':
            raise serializers.ValidationError(
                "Ce compte est déjà suspendu."
            )
        return data


# ============================================
# SERIALIZER RÉACTIVATION COMPTE
# ============================================
class ReactiverCompteSerializer(serializers.Serializer):

    # Motif optionnel
    motif = serializers.CharField(
                max_length=255,
                required=False,
                allow_blank=True
            )

    def validate(self, data):
        compte = self.context.get('compte')

        # Vérifier que le compte existe
        if not compte:
            raise serializers.ValidationError("Compte introuvable.")

        # RG3 — impossible de réactiver un compte déjà actif
        if compte.statut == 'ACTIF':
            raise serializers.ValidationError(
                "Ce compte est déjà actif."
            )
        return data