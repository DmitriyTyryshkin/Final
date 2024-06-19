from django.db import models


class Models_list(models.Model):
    name = models.CharField(max_length=50)
    mse = models.FloatField()
    mae = models.FloatField()
    r2 = models.FloatField()


class News_list(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.CharField(max_length=12)
    end_date = models.CharField(max_length=12)