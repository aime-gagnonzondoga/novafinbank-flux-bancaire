from django.contrib import admin
from .models import Utilisateur, Client, Agent

admin.site.register(Utilisateur)
admin.site.register(Client)
admin.site.register(Agent)