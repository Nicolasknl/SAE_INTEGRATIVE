from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('salle/<str:salle_nom>/', views.salle_detail, name='salle_detail'),
    path('salle/<str:salle_nom>/export/', views.export_salle_csv, name='export_salle_csv'),
    path('donnee/supprimer/<int:donnee_id>/', views.supprimer_donnee, name='supprimer_donnee'),
    path('capteur/modifier/<str:capteur_id>/', views.modifier_capteur, name='modifier_capteur'),
    path('salle/<str:salle_nom>/supprimer-tout/', views.supprimer_toutes_donnees, name='supprimer_toutes_donnees'),
]