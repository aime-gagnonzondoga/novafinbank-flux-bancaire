# serializers permet de convertir les objets Python en JSON et vice versa
from rest_framework import serializers

# On importe Decimal pour les calculs financiers précis
from decimal import Decimal

# On importe le modèle Transfert
from .models import Transfert

# On importe Compte car Transfert implique deux comptes
from comptes.models import Compte

# On importe Parametre pour récupérer les frais configurables (RG6)
from rapports.models import Parametre


# ============================================
# SERIALIZER TRANSFERT
# ============================================
class TransfertSerializer(serializers.ModelSerializer):

    # Numéro du compte source au lieu de son id
    compte_source_numero = serializers.SerializerMethodField()

    # Numéro du compte destination au lieu de son id
    compte_dest_numero   = serializers.SerializerMethodField()

    class Meta:
        model  = Transfert
        fields = [
            'id',
            'reference',
            'montant',
            'frais',
            'statut',
            'date_heure',
            'compte_source_numero',
            'compte_dest_numero',
        ]
        read_only_fields = [
            'id',
            'reference',
            'frais',
            'statut',
            'date_heure',
            'compte_source_numero',
            'compte_dest_numero',
        ]

    def get_compte_source_numero(self, obj):
        """Retourne le numéro du compte source"""
        return obj.compte_source.numero

    def get_compte_dest_numero(self, obj):
        """Retourne le numéro du compte destination"""
        return obj.compte_dest.numero


# ============================================
# SERIALIZER EFFECTUER TRANSFERT
# ============================================
class EffectuerTransfertSerializer(serializers.Serializer):

    # ID du compte source
    compte_source_id = serializers.IntegerField()

    # ID du compte destination
    compte_dest_id   = serializers.IntegerField()

    # Montant — strictement positif (RG6)
    montant          = serializers.DecimalField(max_digits=15, decimal_places=2)

    def validate_montant(self, value):
        # RG6 — montant strictement positif
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant du transfert doit être strictement positif."
            )
        return value

    def validate_compte_source_id(self, value):
        # Une seule requête au lieu de deux
        try:
            compte = Compte.objects.get(id=value)
        except Compte.DoesNotExist:
            raise serializers.ValidationError(
                "Le compte source n'existe pas."
            )

        # RG6 — compte source doit être actif
        if compte.statut != 'ACTIF':
            raise serializers.ValidationError(
                "Le compte source est suspendu — opération refusée."
            )
        return value

    def validate_compte_dest_id(self, value):
        # Une seule requête au lieu de deux
        try:
            compte = Compte.objects.get(id=value)
        except Compte.DoesNotExist:
            raise serializers.ValidationError(
                "Le compte destination n'existe pas."
            )

        # RG6 — compte destination doit être actif
        if compte.statut != 'ACTIF':
            raise serializers.ValidationError(
                "Le compte destination est suspendu — opération refusée."
            )
        return value

    def validate(self, data):
        compte_source_id = data['compte_source_id']
        compte_dest_id   = data['compte_dest_id']
        montant          = data['montant']

        # RG6 — même compte interdit
        if compte_source_id == compte_dest_id:
            raise serializers.ValidationError(
                "Le transfert vers le même compte est interdit."
            )

        # select_related('client') → récupère client en même temps
        # évite une requête supplémentaire pour accéder à compte.client
        compte_source = Compte.objects.select_related('client').get(
            id=compte_source_id
        )
        compte_dest = Compte.objects.select_related('client').get(
            id=compte_dest_id
        )

        # RG6 — calcul des frais
        if compte_source.client != compte_dest.client:
            # Inter-clients → frais = 100 + 0.3% × montant
            try:
                frais_fixe = Decimal(
                    Parametre.objects.get(cle='FRAIS_TRANSFERT_FIXE').valeur
                )
            except Parametre.DoesNotExist:
                frais_fixe = Decimal('100')

            try:
                taux_frais = Decimal(
                    Parametre.objects.get(cle='TAUX_FRAIS_TRANSFERT').valeur
                )
            except Parametre.DoesNotExist:
                taux_frais = Decimal('0.003')

            frais = frais_fixe + (montant * taux_frais)
        else:
            # Même client → gratuit
            frais = Decimal('0')

        # RG6 — solde suffisant pour montant + frais
        montant_total = montant + frais
        if compte_source.solde < montant_total:
            raise serializers.ValidationError(
                f"Solde insuffisant. Montant requis : {montant_total} FCFA "
                f"(montant : {montant} + frais : {frais})."
            )

        # Stockage pour réutilisation dans la vue
        data['frais']         = frais
        data['compte_source'] = compte_source
        data['compte_dest']   = compte_dest

        return data