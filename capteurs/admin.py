from django.contrib import admin
from .models import Capteurs, Donnees


@admin.register(Capteurs)
class CapteursAdmin(admin.ModelAdmin):
    list_display = ('id_capteur', 'nom', 'emplacement')
    search_fields = ('nom', 'emplacement')

@admin.register(Donnees)
class DonneesAdmin(admin.ModelAdmin):
    list_display = ('id_donnee', 'timestamp', 'temperature', 'id_capteur')
    list_filter = ('id_capteur__emplacement', 'timestamp')