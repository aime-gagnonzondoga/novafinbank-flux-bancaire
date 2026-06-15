# uuid est un module Python intégré qui génère des identifiants uniques
# On l'utilise pour créer les références de transactions (TXN-XXXXXXXXXX)
import uuid

# models est le module Django qui permet de définir les tables de la base de données
# Chaque classe qui hérite de models.Model devient une table PostgreSQL
from django.db import models

# ValidationError permet de déclencher une erreur quand une règle métier est violée
# C'est ce qu'on lève dans clean() quand les données sont incorrectes
from django.core.exceptions import ValidationError

# On importe Compte car Transaction a une ForeignKey vers Compte
# Chaque transaction est liée à un compte précis
from comptes.models import Compte

# On importe Transfert car certaines transactions sont liées à un transfert
# Spécifiquement les types TRANSFERT_DEBIT et TRANSFERT_CREDIT (RG6)
from transferts.models import Transfert


# ============================================
# GÉNÉRATEUR DE RÉFÉRENCE UNIQUE
# ============================================

# Fonction qui génère automatiquement une référence unique pour chaque transaction
# uuid.uuid4() génère un identifiant aléatoire universel
# .hex[:10] prend les 10 premiers caractères hexadécimaux
# .upper() les met en majuscules
# Résultat exemple : TXN-A3F9B2C1D4
# Conforme à RG7 — chaque transaction possède une référence unique
def generer_reference_transaction():
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"


# ============================================
# MODÈLE TRANSACTION
# ============================================

# Transaction hérite de models.Model
# Cela dit à Django : "crée une table 'transaction' dans PostgreSQL"
# Conforme à RG7 — toute opération bancaire génère une transaction
class Transaction(models.Model):

    # TYPE_CHOICES définit les valeurs autorisées pour le champ 'type'
    # Format : ('valeur_en_BD', 'Affichage lisible')
    # Conforme à RG7 — les types sont : DEPOT, RETRAIT, TRANSFERT_DEBIT, TRANSFERT_CREDIT
    TYPE_CHOICES = [
        ('DEPOT',            'Dépôt'),           # généré par RG4 (dépôt)
        ('RETRAIT',          'Retrait'),          # généré par RG5 (retrait)
        ('TRANSFERT_DEBIT',  'Transfert Débit'),  # généré par RG6 (débit compte source)
        ('TRANSFERT_CREDIT', 'Transfert Crédit'), # généré par RG6 (crédit compte destination)
    ]

    # STATUT_CHOICES définit les valeurs autorisées pour le champ 'statut'
    # Conforme à RG7 — les statuts possibles sont SUCCES ou ECHEC
    STATUT_CHOICES = [
        ('SUCCES', 'Succès'), # opération réussie → solde modifié
        ('ECHEC',  'Échec'),  # opération échouée → solde inchangé (RG7)
    ]

    # Référence unique de la transaction
    # max_length=50 → 50 caractères max (TXN-XXXXXXXXXX = 14 caractères)
    # unique=True → deux transactions ne peuvent pas avoir la même référence
    # default=generer_reference_transaction → référence générée automatiquement à la création
    # editable=False → la référence ne peut pas être modifiée manuellement
    # Conforme à RG7 — chaque transaction possède une référence unique
    reference  = models.CharField(
                     max_length=50,
                     unique=True,
                     default=generer_reference_transaction,
                     editable=False
                 )

    # Type de la transaction — limité aux valeurs de TYPE_CHOICES
    # max_length=20 → TRANSFERT_CREDIT est le plus long (16 caractères)
    # choices=TYPE_CHOICES → Django valide que la valeur est dans la liste
    # Conforme à RG7
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Montant de la transaction
    # DecimalField → type précis pour les calculs financiers (jamais Float !)
    # max_digits=15 → 15 chiffres au total
    # decimal_places=2 → 2 chiffres après la virgule (ex: 150000.00)
    # Conforme à RG7 — le montant est enregistré
    montant    = models.DecimalField(max_digits=15, decimal_places=2)

    # Frais de la transaction
    # default=0 → gratuit par défaut (dépôt et retrait sont gratuits RG4 et RG5)
    # Seuls les transferts inter-clients ont des frais (RG6)
    frais      = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Statut de la transaction — SUCCES ou ECHEC
    # default='SUCCES' → par défaut on suppose que l'opération réussit
    # Conforme à RG7
    statut     = models.CharField(max_length=10, choices=STATUT_CHOICES, default='SUCCES')

    # Date et heure de la transaction
    # auto_now_add=True → Django enregistre automatiquement la date/heure à la création
    # Non modifiable après création
    # Conforme à RG7 — la date/heure est enregistrée
    date_heure = models.DateTimeField(auto_now_add=True)

    # Clé étrangère vers Compte — chaque transaction appartient à un compte
    # on_delete=PROTECT → impossible de supprimer un compte qui a des transactions
    # related_name='transactions' → depuis un compte : compte.transactions.all()
    # Conforme à RG7 — le compte concerné est enregistré
    compte     = models.ForeignKey(
                     Compte,
                     on_delete=models.PROTECT,
                     related_name='transactions'
                 )

    # Clé étrangère vers Transfert — nullable car uniquement pour TRANSFERT_DEBIT/CREDIT
    # on_delete=SET_NULL → si le transfert est supprimé, ce champ devient NULL
    # null=True → autorise NULL en base de données
    # blank=True → autorise le champ vide dans les formulaires Django
    # Conforme à RG6 — les transactions sont liées au transfert correspondant
    transfert  = models.ForeignKey(
                     Transfert,
                     on_delete=models.SET_NULL,
                     related_name='transactions',
                     null=True,
                     blank=True
                 )

    class Meta:
        # Nom exact de la table dans PostgreSQL
        db_table     = 'transaction'

        # Nom lisible dans l'interface Django Admin
        verbose_name = 'Transaction'

        # Tri par défaut — du plus récent au plus ancien (le - signifie décroissant)
        # Conforme à RG8 — affichage antéchronologique par défaut
        ordering     = ['-date_heure']

    # Représentation textuelle d'une transaction
    # Utilisée dans l'interface Django Admin et les logs
    def __str__(self):
        return f"{self.reference} - {self.type} - {self.montant} FCFA - {self.statut}"

    def clean(self):
        # RG7 — montant strictement positif
        # On vérifie d'abord que montant n'est pas None pour éviter une erreur Python
        if self.montant is not None and self.montant <= 0:
            raise ValidationError(
                "Le montant de la transaction doit être strictement positif."
            )

        # RG7 — transaction validée non modifiable
        # self.pk existe seulement si la transaction est déjà en base (modification)
        # Si c'est une création, self.pk est None donc ce bloc ne s'exécute pas
        if self.pk:
            # On récupère l'ancienne version de la transaction en base
            ancienne = Transaction.objects.get(pk=self.pk)
            # Si l'ancienne transaction était SUCCES → on bloque toute modification
            if ancienne.statut == 'SUCCES':
                raise ValidationError(
                    "Une transaction validée ne peut pas être modifiée."
                )

    def est_modifiable(self):
        """RG7 — Une transaction SUCCES est immuable
        Retourne True si la transaction peut être modifiée (statut ECHEC)
        Retourne False si la transaction est immuable (statut SUCCES)
        """
        return self.statut == 'ECHEC'