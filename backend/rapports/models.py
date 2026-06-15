# models est le module Django pour définir les tables PostgreSQL
from django.db import models

# Import groupé depuis utilisateurs — plus propre qu'en deux lignes séparées
from utilisateurs.models import Utilisateur, Agent

# On importe Compte car ActionAgent concerne un compte précis
# Conforme à RG2 — l'action est liée au compte concerné
from comptes.models import Compte


# ============================================
# MODÈLE ACTION AGENT
# ============================================

# ActionAgent représente la table 'action_agent' dans PostgreSQL
# Conforme à RG2 — toute action réalisée par un agent doit être traçable
class ActionAgent(models.Model):

    # Les 3 types d'actions possibles pour un agent
    # Conforme à RG2 — créer, suspendre ou réactiver un compte
    TYPE_ACTION_CHOICES = [
        ('OUVERTURE_COMPTE',    'Ouverture de compte'),    # RG3
        ('SUSPENSION_COMPTE',   'Suspension de compte'),   # RG2
        ('REACTIVATION_COMPTE', 'Réactivation de compte'), # RG2
    ]

    # Type d'action — limité aux 3 valeurs définies ci-dessus
    # max_length=25 → REACTIVATION_COMPTE = 20 caractères
    type_action = models.CharField(
                      max_length=25,
                      choices=TYPE_ACTION_CHOICES
                  )

    # Date et heure de l'action — enregistrée automatiquement
    # auto_now_add=True → non modifiable après création
    # Garantit l'intégrité de la traçabilité (RG2)
    date        = models.DateTimeField(auto_now_add=True)

    # Description libre de l'action — optionnelle
    # TextField → pas de limite de caractères
    description = models.TextField(blank=True, null=True)

    # Agent qui a réalisé l'action
    # PROTECT → impossible de supprimer un agent qui a des actions tracées
    # related_name='actions' → agent.actions.all()
    agent       = models.ForeignKey(
                      Agent,
                      on_delete=models.PROTECT,
                      related_name='actions'
                  )

    # Compte concerné par l'action
    # PROTECT → impossible de supprimer un compte qui a des actions tracées
    # related_name='actions_agent' → compte.actions_agent.all()
    compte      = models.ForeignKey(
                      Compte,
                      on_delete=models.PROTECT,
                      related_name='actions_agent'
                  )

    class Meta:
        db_table     = 'action_agent'
        verbose_name = 'Action Agent'
        ordering     = ['-date'] # plus récent en premier

    def __str__(self):
        return f"{self.agent} - {self.type_action} - {self.date}"


# ============================================
# MODÈLE LOG SECURITE
# ============================================

# LogSecurite représente la table 'log_securite' dans PostgreSQL
# Conforme à RG9 — toute connexion/déconnexion/tentative échouée est enregistrée
class LogSecurite(models.Model):

    # Les 3 types d'événements de sécurité
    # Conforme à RG9
    ACTION_CHOICES = [
        ('CONNEXION',       'Connexion'),        # utilisateur connecté
        ('DECONNEXION',     'Déconnexion'),       # utilisateur déconnecté
        ('TENTATIVE_ECHEC', 'Tentative échouée'), # connexion échouée
    ]

    # Type d'événement — limité aux 3 valeurs définies
    # max_length=20 → TENTATIVE_ECHEC = 15 caractères
    action      = models.CharField(
                      max_length=20,
                      choices=ACTION_CHOICES
                  )

    # Date et heure de l'événement — enregistrée automatiquement
    # Conforme à RG9 — horodatage obligatoire
    date_heure  = models.DateTimeField(auto_now_add=True)

    # Adresse IP de l'utilisateur au moment de l'événement
    # max_length=50 → IPv4 (15 chars) et IPv6 (39 chars)
    # null=True → peut être inconnue (tentative sans IP détectable)
    adresse_ip  = models.CharField(max_length=50, blank=True, null=True)

    # Navigateur/appareil utilisé — ajout professionnel pour la sécurité bancaire
    # Permet d'identifier les connexions suspectes
    # null=True → optionnel
    user_agent  = models.CharField(max_length=255, blank=True, null=True)

    # Détails supplémentaires sur l'événement
    details     = models.TextField(blank=True, null=True)

    # Utilisateur concerné par l'événement
    # SET_NULL → si utilisateur supprimé le log est conservé (important pour audit)
    # null=True → tentative avec email inexistant → utilisateur inconnu
    utilisateur = models.ForeignKey(
                      Utilisateur,
                      on_delete=models.SET_NULL,
                      related_name='logs',
                      null=True,
                      blank=True
                  )

    class Meta:
        db_table     = 'log_securite'
        verbose_name = 'Log de sécurité'
        ordering     = ['-date_heure'] # plus récent en premier

    def __str__(self):
        return f"{self.action} - {self.utilisateur} - {self.date_heure}"


# ============================================
# MODÈLE PARAMETRE
# ============================================

# Parametre représente la table 'parametre' dans PostgreSQL
# Conforme à RG9 — l'administrateur configure les paramètres globaux
class Parametre(models.Model):

    # Clé unique du paramètre — identifiant lisible
    # unique=True → pas de doublon possible
    # Exemples : PLAFOND_RETRAIT_JOURNALIER, DEPOT_INITIAL_MINIMUM
    cle         = models.CharField(max_length=100, unique=True)

    # Valeur du paramètre sous forme de texte
    # CharField car les valeurs peuvent être nombres ou texte
    # Exemples : "5000000", "1500", "100", "0.003"
    valeur      = models.CharField(max_length=255)

    # Description du rôle du paramètre — optionnelle
    description = models.TextField(blank=True, null=True)

    # Date de dernière modification
    # auto_now=True → mis à jour automatiquement à chaque save()
    # Différent de auto_now_add qui ne s'enregistre qu'à la création
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'parametre'
        verbose_name = 'Paramètre'
        ordering     = ['cle'] # tri alphabétique

    def __str__(self):
        return f"{self.cle} = {self.valeur}"