from django.contrib import admin
from .models import Capteurs, Donnees

# On enregistre les modèles pour qu'ils apparaissent dans le panel admin
@admin.register(Capteurs)
class CapteursAdmin(admin.ModelAdmin):
    list_display = ('id_capteur', 'nom', 'emplacement') # Les colonnes visibles dans la liste
    search_fields = ('nom', 'emplacement')               # Barre de recherche pratique

@admin.register(Donnees)
class DonneesAdmin(admin.ModelAdmin):
    list_display = ('id_donnee', 'timestamp', 'temperature', 'id_capteur')
    list_filter = ('id_capteur__emplacement', 'timestamp') # Filtres sur le côté droit