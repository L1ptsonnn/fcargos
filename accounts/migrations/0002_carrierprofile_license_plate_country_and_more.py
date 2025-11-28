# Згенеровано Django 4.2.7 2025-11-02 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrierprofile',
            name='license_plate_country',
            field=models.CharField(default='UA', max_length=10, verbose_name='Країна номерного знака'),
        ),
        migrations.AddField(
            model_name='carrierprofile',
            name='license_plate_number',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Номерний знак'),
        ),
        migrations.AddField(
            model_name='carrierprofile',
            name='vehicle_model',
            field=models.CharField(blank=True, default='', max_length=150, verbose_name='Модель машини'),
        ),
    ]
