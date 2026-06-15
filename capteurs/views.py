from django.shortcuts import render
import csv
from django.http import HttpResponse


def index(request):
    # Logique pour la page d'accueil (Calcul des moyennes des deux salles, etc.)
    context = {
        'moyenne_salle1': "24.2",
        'moyenne_salle2': "19.5",
    }
    return render(request, 'capteurs/index.html', context)


def salle_detail(request, salle_id):
    # 1. Récupération des filtres saisis par l'utilisateur dans l'URL
    search_query = request.GET.get('search', '').strip()
    date_debut = request.GET.get('date_debut', '')  # Format reçu : YYYY-MM-DDTHH:MM
    date_fin = request.GET.get('date_fin', '')      # Format reçu : YYYY-MM-DDTHH:MM

    # 2. Notre "Fausse" Base de données MySQL (Plus riche pour pouvoir tester les filtres)
    # On utilise 'date_iso' au format YYYY-MM-DDTHH:MM pour trier et filtrer super facilement en Python
    if salle_id == 1:
        toutes_les_mesures = [
            {'id': '12345', 'nom': 'Capteur1', 'valeur': 24.5, 'date_iso': '2026-06-15T15:32', 'date': '15/06/2026 15:32'},
            {'id': '12A6B8', 'nom': 'Capteur_Salon_Fenetre', 'valeur': 23.9, 'date_iso': '2026-06-15T15:31', 'date': '15/06/2026 15:31'},
            {'id': '12345', 'nom': 'Capteur1', 'valeur': 21.0, 'date_iso': '2026-06-14T10:00', 'date': '14/06/2026 10:00'},
            {'id': '12A6B8', 'nom': 'Capteur_Salon_Fenetre', 'valeur': 20.5, 'date_iso': '2026-06-13T09:15', 'date': '13/06/2026 09:15'},
        ]
    else:
        toutes_les_mesures = [
            {'id': '89F2C1', 'nom': 'Capteur_Cuisine_Principal', 'valeur': 19.2, 'date_iso': '2026-06-15T15:31', 'date': '15/06/2026 15:31'},
            {'id': '89F2C1', 'nom': 'Capteur_Cuisine_Principal', 'valeur': 18.5, 'date_iso': '2026-06-14T22:45', 'date': '14/06/2026 22:45'},
            {'id': '89F2C1', 'nom': 'Capteur_Cuisine_Principal', 'valeur': 17.9, 'date_iso': '2026-06-12T11:30', 'date': '12/06/2026 11:30'},
        ]

    # 3. APPLICATION DES FILTRES (Logique cumulable)
    mesures_filtrees = toutes_les_mesures

    # Filtre de recherche (ID ou Nom du capteur)
    if search_query:
        mesures_filtrees = [
            m for m in mesures_filtrees
            if search_query.lower() in m['id'].lower() or search_query.lower() in m['nom'].lower()
        ]

    # Filtre Date Début (On compare les chaînes ISO qui ont le même format)
    if date_debut:
        mesures_filtrees = [m for m in mesures_filtrees if m['date_iso'] >= date_debut]

    # Filtre Date Fin
    if date_fin:
        mesures_filtrees = [m for m in mesures_filtrees if m['date_iso'] <= date_fin]

    # 4. CALCUL DE LA MOYENNE DYNAMIQUE
    # Elle s'adapte automatiquement en fonction des lignes restantes après filtrage !
    if mesures_filtrees:
        total_temp = sum(m['valeur'] for m in mesures_filtrees)
        moyenne_calculee = round(total_temp / len(mesures_filtrees), 1)
    else:
        moyenne_calculee = "--.-"

    context = {
        'salle_id': salle_id,
        'mesures': mesures_filtrees,
        'moyenne_salle': moyenne_calculee,
    }
    return render(request, 'capteurs/salle.html', context)


def export_salle_csv(request, salle_id):
    # 1. On récupère les filtres (pour pouvoir exporter uniquement ce qui est filtré à l'écran)
    search_query = request.GET.get('search', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="export_salle_{salle_id}.csv"'

    # On utilise le writer CSV (avec encodage utf-8-sig pour que Excel lise bien les accents)
    writer = csv.writer(response, delimiter=';')

    # Écriture de la ligne d'entête du tableau
    writer.writerow(['ID Capteur', 'Nom du Capteur', 'Valeur Enregistree (C)', 'Date et Heure'])

    # 3. DONNÉES FICTIVES (À remplacer par ta requête MySQL plus tard)
    # On simule ce que la BDD renverrait selon la salle
    if salle_id == 1:
        mesures_simulees = [
            ['12345', 'Capteur1', '24.5', '15/06/2026 15:32:01'],
            ['12A6B8', 'Capteur_Salon_Fenetre', '23.9', '15/06/2026 15:31:41']
        ]
    else:
        mesures_simulees = [
            ['89F2C1', 'Capteur_Cuisine_Principal', '19.2', '15/06/2026 15:31:56']
        ]

    # 4. Écriture des données dans le fichier
    for ligne in mesures_simulees:
        writer.writerow(ligne)

    return response