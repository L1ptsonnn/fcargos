# Згенеровано Django 4.2.7 2025-11-01 11:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logistics', '0004_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('new_bid', 'Нова ставка'), ('bid_accepted', 'Вашу ставку прийнято'), ('bid_rejected', 'Вашу ставку відхилено'), ('new_message', 'Нове повідомлення'), ('route_assigned', 'Вам призначено маршрут'), ('route_completed', 'Маршрут завершено'), ('tracking_updated', 'Оновлено відстеження')], max_length=20, verbose_name='Тип сповіщення')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('message', models.TextField(verbose_name='Текст сповіщення')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('route', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='logistics.route', verbose_name='Маршрут')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Сповіщення',
                'verbose_name_plural': 'Сповіщення',
                'ordering': ['-created_at'],
            },
        ),
    ]
