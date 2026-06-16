from django.db import migrations

def inserer_parametres(apps, schema_editor):
    Parametre = apps.get_model('rapports', 'Parametre')
    parametres = [
        ('PLAFOND_RETRAIT_JOURNALIER', '5000000', 'Plafond retrait journalier RG5'),
        ('DEPOT_INITIAL_MINIMUM',      '1500',    'Dépôt initial minimum RG3'),
        ('FRAIS_TRANSFERT_FIXE',       '100',     'Frais fixes transfert RG6'),
        ('TAUX_FRAIS_TRANSFERT',       '0.003',   'Taux frais transfert RG6'),
    ]
    for cle, valeur, description in parametres:
        Parametre.objects.get_or_create(
            cle=cle,
            defaults={
                'valeur':      valeur,
                'description': description,
            }
        )

class Migration(migrations.Migration):
    dependencies = [
        ('rapports', '0002_initial'),
    ]
    operations = [
        migrations.RunPython(inserer_parametres),
    ]