from django.urls import path

from .views import (
    ListeActionsAgentView,
    ListeLogsSecuriteView,
    ListeParametresView,
    ModifierParametreView,
    ListeToutesActionsView,
)

app_name = 'rapports'

urlpatterns = [

    # ── Actions de l'agent connecté ──
    # GET /api/rapports/actions/
    path('actions/', ListeActionsAgentView.as_view(), name='actions-agent'),

    # ── Toutes les actions — Admin uniquement ──
    # GET /api/rapports/actions/toutes/
    # IMPORTANT : 'toutes/' avant tout paramètre dynamique
    path('actions/toutes/', ListeToutesActionsView.as_view(), name='toutes-actions'),

    # ── Logs de sécurité — Admin uniquement ──
    # GET /api/rapports/logs/
    path('logs/', ListeLogsSecuriteView.as_view(), name='logs-securite'),

    # ── Liste des paramètres — Admin uniquement ──
    # GET /api/rapports/parametres/
    path('parametres/', ListeParametresView.as_view(), name='liste-parametres'),

    # ── Modifier un paramètre — Admin uniquement ──
    # PATCH /api/rapports/parametres/PLAFOND_RETRAIT_JOURNALIER/
    # <str:cle> car la clé est une chaîne de caractères
    path('parametres/<str:cle>/', ModifierParametreView.as_view(), name='modifier-parametre'),
]