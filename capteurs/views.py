from django.shortcuts import render, get_object_or_404, redirect
import csv
from django.http import HttpResponse
from django.db.models import Q, Avg
from .models import Capteurs, Donnees
from django.utils import timezone
from datetime import timedelta


def index(request):

    stats_salles = Donnees.objects.values('id_capteur__emplacement').annotate(
        moyenne_temp=Avg('temperature')
    ).order_by('id_capteur__emplacement')

    salles_data = []
    for s in stats_salles:
        nom_piece = s['id_capteur__emplacement']
        if nom_piece:
            salles_data.append({
                'nom': nom_piece,
                'moyenne': round(s['moyenne_temp'], 1) if s['moyenne_temp'] is not None else "--.-"
            })

    # 2. Récupération des 5 derniers relevés globaux de la BDD
    derniers_releves = Donnees.objects.select_related('id_capteur').order_by('-timestamp')[:5]

    derniers_messages = []
    for r in derniers_releves:
        derniers_messages.append({
            'heure': r.timestamp.strftime('%H:%M:%S') if r.timestamp else '--:--:--',
            'id': r.id_capteur.id_capteur,
            'salle': r.id_capteur.emplacement if r.id_capteur.emplacement else "Sans salle",
            'temp': r.temperature
        })

    # 3. Envoi au template index.html
    context = {
        'salles': salles_data,
        'derniers_messages': derniers_messages
    }
    return render(request, 'capteurs/index.html', context)


def salle_detail(request, salle_nom):

    search_query = request.GET.get('search', '').strip()
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    # 2. Requête de base pour la salle courante
    mesures_queryset = Donnees.objects.filter(id_capteur__emplacement=salle_nom).select_related('id_capteur').order_by(
        '-timestamp')

    # 3. Filtres ORM cumulables
    if search_query:
        mesures_queryset = mesures_queryset.filter(
            Q(id_capteur__id_capteur__icontains=search_query) |
            Q(id_capteur__nom__icontains=search_query)
        )

    if date_debut:
        mesures_queryset = mesures_queryset.filter(timestamp__gte=date_debut)

    if date_fin:
        mesures_queryset = mesures_queryset.filter(timestamp__lte=date_fin)

    # 4. Calcul de la moyenne dynamique sur les données filtrées
    moyenne_recuperee = mesures_queryset.aggregate(Avg('temperature'))['temperature__avg']
    moyenne_calculee = round(moyenne_recuperee, 1) if moyenne_recuperee is not None else "--.-"

    # 5. PRÉPARATION DES DONNÉES DU GRAPHIQUE (Limité aux 3 dernières heures par défaut)
    if not date_debut and not date_fin:
        # Si aucun filtre de date n'est mis, on prend NOW - 3 heures
        il_y_a_3_heures = timezone.now() - timedelta(hours=2)
        mesures_chrono = mesures_queryset.filter(timestamp__gte=il_y_a_3_heures).order_by('timestamp')
    else:
        # Si l'utilisateur a mis un filtre, le graphique s'adapte à sa demande
        mesures_chrono = mesures_queryset.order_by('timestamp')

    # ASTUCE : On affiche juste '%H:%M' au lieu de la date complète pour alléger l'axe X
    graph_dates = [m.timestamp.strftime('%H:%M') for m in mesures_chrono]
    graph_temps = [float(m.temperature) for m in mesures_chrono]

    # 6. Adaptation du format pour le tableau HTML
    mesures_filtrees = []
    for m in mesures_queryset:
        mesures_filtrees.append({
            'id_brut': m.id_donnee,  # Clé primaire nécessaire pour la suppression
            'id': m.id_capteur.id_capteur,
            'nom': m.id_capteur.nom,
            'valeur': m.temperature,
            'date_iso': m.timestamp.strftime('%Y-%m-%dT%H:%M') if m.timestamp else '',
            'date': m.timestamp.strftime('%d/%m/%Y %H:%M') if m.timestamp else ''
        })

    context = {
        'salle_nom': salle_nom,
        'mesures': mesures_filtrees,
        'moyenne_salle': moyenne_calculee,
        'graph_dates': graph_dates,
        'graph_temps': graph_temps,
    }
    
    return render(request, 'capteurs/salle.html', context)


def export_salle_csv(request, salle_nom):
    # 1. Récupération des filtres pour l'export
    search_query = request.GET.get('search', '').strip()
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    mesures_queryset = Donnees.objects.filter(id_capteur__emplacement=salle_nom).select_related('id_capteur').order_by(
        '-timestamp')

    if search_query:
        mesures_queryset = mesures_queryset.filter(
            Q(id_capteur__id_capteur__icontains=search_query) |
            Q(id_capteur__nom__icontains=search_query)
        )
    if date_debut:
        mesures_queryset = mesures_queryset.filter(timestamp__gte=date_debut)
    if date_fin:
        mesures_queryset = mesures_queryset.filter(timestamp__lte=date_fin)

    # 2. Préparation du fichier CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="export_{salle_nom}.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Capteur', 'Nom du Capteur', 'Valeur Enregistree (C)', 'Date et Heure'])

    # 3. Écriture des données
    for m in mesures_queryset:
        date_excel = m.timestamp.strftime('%d/%m/%Y %H:%M:%S') if m.timestamp else ''
        writer.writerow([
            m.id_capteur.id_capteur,
            m.id_capteur.nom,
            m.temperature,
            date_excel
        ])

    return response


# --- NOUVELLES FONCTIONS CRUD ---

def supprimer_donnee(request, donnee_id):
    """Supprime un relevé de température spécifique et redirige vers la salle"""
    donnee = get_object_or_404(Donnees, id_donnee=donnee_id)
    salle_nom = donnee.id_capteur.emplacement
    donnee.delete()
    return redirect('salle_detail', salle_nom=salle_nom)


def modifier_capteur(request, capteur_id):
    """Gère la modification du nom et de la pièce d'un capteur"""
    capteur = get_object_or_404(Capteurs, id_capteur=capteur_id)

    if request.method == 'POST':
        capteur.nom = request.POST.get('nom_capteur')
        capteur.emplacement = request.POST.get('emplacement_capteur')
        capteur.save()
        # Redirige vers la nouvelle pièce assignée au capteur
        return redirect('salle_detail', salle_nom=capteur.emplacement)

    return render(request, 'capteurs/modifier_capteur.html', {'capteur': capteur})