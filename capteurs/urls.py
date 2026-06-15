from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('salle/<int:salle_id>/', views.salle_detail, name='salle_detail'),
    path('salle/<int:salle_id>/export/', views.export_salle_csv, name='export_salle_csv'),
]