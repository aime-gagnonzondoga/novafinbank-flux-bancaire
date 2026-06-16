# serializers permet de convertir les objets Python en JSON et vice versa
from rest_framework import serializers

# On importe Decimal pour les calculs financiers précis
from decimal import Decimal

# On importe date pour les calculs de plafond journalier
from datetime import date

# Import Sum en haut du fichier — bonne pratique Python
from django.db.models import Sum

# On importe le modèle Transaction
from .models import Transaction

# On importe Compte car Transaction est liée à un compte
from comptes.models import Compte

# On importe Parametre pour récupérer le plafond journalier configurable (RG5)
from rapports.models import Parametre


# ============================================
# SERIALIZER TRANSACTION
# ============================================
class TransactionSerializer(serializers.ModelSerializer):

    # Numéro du compte au lieu de son id
    compte_numero = serializers.SerializerMethodField()

    class Meta:
        model  = Transaction
        fields = [
            'id',
            'reference',
            'type',
            'montant',
            'frais',
            'statut',
            'date_heure',
            'compte_numero',
        ]
        # RG7 — transaction validée immuable
        read_only_fields = [
            'id',
            'reference',
            'type',
            'montant',
            'frais',
            'statut',
            'date_heure',
            'compte_numero',
        ]

    def get_compte_numero(self, obj):
        """Retourne le numéro du compte concerné"""
        return obj.compte.numero


# ============================================
# SERIALIZER DÉPÔT
# ============================================
class DepotSerializer(serializers.Serializer):

    # ID du compte bénéficiaire
    compte_id = serializers.IntegerField()

    # Montant — strictement positif (RG4)
    montant   = serializers.DecimalField(max_digits=15, decimal_places=2)

    def validate_compte_id(self, value):
        # Une seule requête
        try:
            compte = Compte.objects.get(id=value)
        except Compte.DoesNotExist:
            raise serializers.ValidationError(
                "Ce compte n'existe pas."
            )

        # RG4 — compte bénéficiaire actif
        if compte.statut != 'ACTIF':
            raise serializers.ValidationError(
                "Le compte est suspendu — aucune opération autorisée."
            )

        # Stocker pour réutilisation dans validate()
        self._compte = compte
        return value

    def validate_montant(self, value):
        # RG4 — montant strictement positif
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant du dépôt doit être strictement positif."
            )
        return value

    def validate(self, data):
        # Stocker le compte pour la vue
        data['compte'] = self._compte
        return data


# ============================================
# SERIALIZER RETRAIT
# ============================================
class RetraitSerializer(serializers.Serializer):

    # ID du compte concerné
    compte_id = serializers.IntegerField()

    # Montant — strictement positif (RG5)
    montant   = serializers.DecimalField(max_digits=15, decimal_places=2)

    def validate_montant(self, value):
        # RG5 — montant strictement positif
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant du retrait doit être strictement positif."
            )
        return value

    def validate_compte_id(self, value):
        # Une seule requête
        try:
            compte = Compte.objects.get(id=value)
        except Compte.DoesNotExist:
            raise serializers.ValidationError(
                "Ce compte n'existe pas."
            )

        # RG5 — compte actif
        if compte.statut != 'ACTIF':
            raise serializers.ValidationError(
                "Le compte est suspendu — aucune opération autorisée."
            )

        # Stocker pour éviter une 2ème requête dans validate()
        self._compte = compte
        return value

    def validate(self, data):
        # Utiliser le compte déjà récupéré — pas de 2ème requête
        compte  = self._compte
        montant = data['montant']

        # RG5 — solde suffisant
        if compte.solde < montant:
            raise serializers.ValidationError(
                f"Solde insuffisant. Solde disponible : {compte.solde} FCFA."
            )

        # RG5 — plafond journalier
        aujourd_hui = date.today()

        # Cumul des retraits SUCCES d'aujourd'hui sur ce compte
        # Sum importé en haut du fichier — bonne pratique
        total_retire_aujourd_hui = Transaction.objects.filter(
            compte=compte,
            type='RETRAIT',
            statut='SUCCES',
            date_heure__date=aujourd_hui
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0')

        # Plafond depuis Parametre
        try:
            plafond = Decimal(
                Parametre.objects.get(cle='PLAFOND_RETRAIT_JOURNALIER').valeur
            )
        except Parametre.DoesNotExist:
            plafond = Decimal('5000000')

        # Vérifier cumul + nouveau montant
        if total_retire_aujourd_hui + montant > plafond:
            restant = plafond - total_retire_aujourd_hui
            raise serializers.ValidationError(
                f"Plafond journalier de {plafond} FCFA dépassé. "
                f"Vous pouvez encore retirer : {restant} FCFA aujourd'hui."
            )

        # Stocker le compte pour la vue
        data['compte'] = compte
        return data


# ============================================
# SERIALIZER HISTORIQUE
# ============================================
class HistoriqueSerializer(serializers.Serializer):

    # ID du compte dont on veut l'historique
    compte_id  = serializers.IntegerField()

    # Date de début — optionnelle (RG8)
    date_debut = serializers.DateField(required=False, allow_null=True)

    # Date de fin — optionnelle (RG8)
    date_fin   = serializers.DateField(required=False, allow_null=True)

    # Ordre d'affichage (RG8)
    ordre      = serializers.ChoiceField(
                     choices=['chronologique', 'antéchronologique'],
                     required=False,
                     default='antéchronologique'
                 )

    def validate_compte_id(self, value):
        # Vérifier que le compte existe
        try:
            Compte.objects.get(id=value)
        except Compte.DoesNotExist:
            raise serializers.ValidationError(
                "Ce compte n'existe pas."
            )
        return value

    def validate(self, data):
        date_debut = data.get('date_debut')
        date_fin   = data.get('date_fin')

        # RG8 — date_debut doit être avant date_fin
        if date_debut and date_fin:
            if date_debut > date_fin:
                raise serializers.ValidationError(
                    "La date de début doit être antérieure à la date de fin."
                )
        return data