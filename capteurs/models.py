from django.db import models

class Capteurs(models.Model):
    id_capteur = models.CharField(primary_key=True, max_length=50)
    nom = models.CharField(unique=True, max_length=100, blank=True, null=True)
    emplacement = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'capteurs'


class Donnees(models.Model):
    id_donnee = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    temperature = models.FloatField()
    id_capteur = models.ForeignKey(Capteurs, models.DO_NOTHING, db_column='id_capteur', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'donnees'