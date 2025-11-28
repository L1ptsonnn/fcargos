# Згенеровано Django 4.2.7 2025-11-01 12:54

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logistics', '0005_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(help_text='Оцінка від 1 до 5', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Оцінка')),
                ('comment', models.TextField(blank=True, verbose_name='Коментар')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('carrier', models.ForeignKey(limit_choices_to={'role': 'carrier'}, on_delete=django.db.models.deletion.CASCADE, related_name='ratings_received', to=settings.AUTH_USER_MODEL, verbose_name='Перевізник')),
                ('company', models.ForeignKey(limit_choices_to={'role': 'company'}, on_delete=django.db.models.deletion.CASCADE, related_name='ratings_given', to=settings.AUTH_USER_MODEL, verbose_name='Компанія')),
                ('route', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='logistics.route', verbose_name='Маршрут')),
            ],
            options={
                'verbose_name': 'Оцінка',
                'verbose_name_plural': 'Оцінки',
                'ordering': ['-created_at'],
                'unique_together': {('carrier', 'company', 'route')},
            },
        ),
    ]
