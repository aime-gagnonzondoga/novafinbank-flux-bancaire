import uuid
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from comptes.models import Compte


# ============================================
# GÉNÉRATEUR DE RÉFÉRENCE UNIQUE
# ============================================
def generer_reference_transfert():
    return f"TRF-{uuid.uuid4().hex[:10].upper()}"


# ============================================
# MODÈLE TRANSFERT
# ============================================
class Transfert(models.Model):

    STATUT_CHOICES = [
        ('SUCCES', 'Succès'),
        ('ECHEC',  'Échec'),
    ]

    reference     = models.CharField(
                        max_length=50,
                        unique=True,
                        default=generer_reference_transfert,
                        editable=False
                    )
    montant       = models.DecimalField(max_digits=15, decimal_places=2)
    frais         = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut        = models.CharField(max_length=10, choices=STATUT_CHOICES, default='SUCCES')
    date_heure    = models.DateTimeField(auto_now_add=True)
    compte_source = models.ForeignKey(
                        Compte,
                        on_delete=models.PROTECT,
                        related_name='transferts_emis'
                    )
    compte_dest   = models.ForeignKey(
                        Compte,
                        on_delete=models.PROTECT,
                        related_name='transferts_recus'
                    )

    class Meta:
        db_table     = 'transfert'
        verbose_name = 'Transfert'

    def __str__(self):
        return f"{self.reference} - {self.montant} FCFA - {self.statut}"

    def clean(self):
        # RG6 — montant strictement positif
        if self.montant is not None and self.montant <= 0:
            raise ValidationError(
                "Le montant du transfert doit être strictement positif."
            )
        # RG6 — transfert vers même compte interdit
        if self.compte_source and self.compte_dest:
            if self.compte_source == self.compte_dest:
                raise ValidationError(
                    "Le transfert vers le même compte est interdit."
                )
        # RG6 — aucun frais si transfert échoue
        if self.statut == 'ECHEC':
            self.frais = 0

    def est_inter_client(self):
        """RG6 — Vérifie si les deux comptes appartiennent à des clients différents"""
        return self.compte_source.client != self.compte_dest.client

    def calculer_frais(self):
        """RG6 — Calcule les frais selon le type de transfert"""
        if self.est_inter_client():
            return Decimal('100') + (self.montant * Decimal('0.003'))
        return Decimal('0')