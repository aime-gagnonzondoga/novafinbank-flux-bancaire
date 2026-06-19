# path permet de définir les routes URL
from django.urls import path

# On importe toutes les vues nécessaires
from .views import (
    InscriptionClientView,
    ProfilClientView,
    ProfilAgentView,
    CreerAgentView,
    ListeUtilisateursView,
)

# app_name permet de nommer les URLs pour les retrouver facilement
app_name = 'utilisateurs'

urlpatterns = [

    # ── Inscription client (public — AllowAny) ──
    # POST /api/clients/inscription/
    path('clients/inscription/', InscriptionClientView.as_view(), name='inscription-client'),

    # ── Profil client connecté ──
    # GET  /api/clients/profil/ → voir son profil
    # PATCH /api/clients/profil/ → modifier son profil
    path('clients/profil/', ProfilClientView.as_view(), name='profil-client'),

    # ── Profil agent connecté ──
    # GET  /api/agents/profil/ → voir son profil
    # PATCH /api/agents/profil/ → modifier son profil
    path('agents/profil/', ProfilAgentView.as_view(), name='profil-agent'),

    # ── Créer un agent — Admin uniquement ──
    # POST /api/agents/creer/
    path('agents/creer/', CreerAgentView.as_view(), name='creer-agent'),

    # ── Liste utilisateurs — Admin uniquement ──
    # GET /api/utilisateurs/
    path('utilisateurs/', ListeUtilisateursView.as_view(), name='liste-utilisateurs'),

    # ── Activer/Désactiver un utilisateur — Admin uniquement ──
    # PATCH /api/utilisateurs/1/
    path('utilisateurs/<int:pk>/', ListeUtilisateursView.as_view(), name='modifier-utilisateur'),
]