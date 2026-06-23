from django.shortcuts import render, get_object_or_404, redirect
import csv
from django.http import HttpResponse
from django.db.models import Q, Avg
from .models import Capteurs, Donnees
from django.utils import timezone
from datetime import timedelta


def index(request):
    salles_existantes = Capteurs.objects.values_list('emplacement', flat=True).distinct().order_by('emplacement')

    salles_data = []
    for nom_piece in salles_existantes:
        if nom_piece:
            moyenne_brute = Donnees.objects.filter(id_capteur__emplacement=nom_piece).aggregate(
                avg_temp=Avg('temperature')
            )['avg_temp']

            salles_data.append({
                'nom': nom_piece,
                'moyenne': round(moyenne_brute, 1) if moyenne_brute is not None else "--.-"
            })

    derniers_releves = Donnees.objects.select_related('id_capteur').order_by('-timestamp')[:5]

    derniers_messages = []
    for r in derniers_releves:
        derniers_messages.append({
            'heure': r.timestamp.strftime('%H:%M:%S') if r.timestamp else '--:--:--',
            'nom': r.id_capteur.nom,
            'salle': r.id_capteur.emplacement if r.id_capteur.emplacement else "Sans salle",
            'temp': r.temperature
        })

    context = {
        'salles': salles_data,
        'derniers_messages': derniers_messages
    }
    return render(request, 'capteurs/index.html', context)


def salle_detail(request, salle_nom):
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

    moyenne_recuperee = mesures_queryset.aggregate(Avg('temperature'))['temperature__avg']
    moyenne_calculee = round(moyenne_recuperee, 1) if moyenne_recuperee is not None else "--.-"

    if not date_debut and not date_fin:
        il_y_a_30_minutes = timezone.now() - timedelta(minutes=30)
        mesures_chrono = mesures_queryset.filter(timestamp__gte=il_y_a_30_minutes).order_by('-timestamp')[:40]
        mesures_chrono = list(reversed(mesures_chrono))
    else:
        mesures_chrono = list(mesures_queryset.order_by('timestamp'))

    graph_dates = [m.timestamp.strftime('%H:%M') for m in mesures_chrono]
    graph_temps = [float(m.temperature) for m in mesures_chrono]

    mesures_filtrees = []
    for m in mesures_queryset:
        mesures_filtrees.append({
            'id_brut': m.id_donnee,
            'id': m.id_capteur.id_capteur,
            'nom': m.id_capteur.nom,
            'valeur': m.temperature,
            'date_iso': m.timestamp.strftime('%Y-%m-%dT%H:%M') if m.timestamp else '',
            'date': m.timestamp.strftime('%d/%m/%Y %H:%M') if m.timestamp else ''
        })
    capteurs_de_la_salle = Capteurs.objects.filter(emplacement=salle_nom)
    context = {
        'salle_nom': salle_nom,
        'mesures': mesures_filtrees,
        'moyenne_salle': moyenne_calculee,
        'graph_dates': graph_dates,
        'graph_temps': graph_temps,
        'liste_capteurs_salle': capteurs_de_la_salle,
    }

    return render(request, 'capteurs/salle.html', context)


def export_salle_csv(request, salle_nom):
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

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="export_{salle_nom}.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Capteur', 'Nom du Capteur', 'Valeur Enregistree (C)', 'Date et Heure'])

    for m in mesures_queryset:
        date_excel = m.timestamp.strftime('%d/%m/%Y %H:%M:%S') if m.timestamp else ''
        writer.writerow([
            m.id_capteur.id_capteur,
            m.id_capteur.nom,
            m.temperature,
            date_excel
        ])

    return response


def supprimer_donnee(request, donnee_id):
    donnee = get_object_or_404(Donnees, id_donnee=donnee_id)
    salle_nom = donnee.id_capteur.emplacement
    donnee.delete()
    return redirect('salle_detail', salle_nom=salle_nom)


def modifier_capteur(request, capteur_id):
    capteur = get_object_or_404(Capteurs, id_capteur=capteur_id)

    if request.method == 'POST':
        capteur.nom = request.POST.get('nom_capteur')
        capteur.emplacement = request.POST.get('emplacement_capteur')
        capteur.save()
        return redirect('salle_detail', salle_nom=capteur.emplacement)

    return render(request, 'capteurs/modifier_capteur.html', {'capteur': capteur})


def supprimer_toutes_donnees(request, salle_nom):
    if request.method == 'POST':
        search_query = request.POST.get('search', '').strip()
        date_debut = request.POST.get('date_debut', '')
        date_fin = request.POST.get('date_fin', '')

        mesures_a_supprimer = Donnees.objects.filter(id_capteur__emplacement=salle_nom)

        if search_query:
            mesures_a_supprimer = mesures_a_supprimer.filter(
                Q(id_capteur__id_capteur__icontains=search_query) |
                Q(id_capteur__nom__icontains=search_query)
            )
        if date_debut:
            mesures_a_supprimer = mesures_a_supprimer.filter(timestamp__gte=date_debut)
        if date_fin:
            mesures_a_supprimer = mesures_a_supprimer.filter(timestamp__lte=date_fin)

        mesures_a_supprimer.delete()

    return redirect('salle_detail', salle_nom=salle_nom)