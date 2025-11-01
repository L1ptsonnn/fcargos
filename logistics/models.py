from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User


class Route(models.Model):
    """Маршрут доставки"""
    STATUS_CHOICES = [
        ('pending', 'Очікує'),
        ('in_transit', 'В дорозі'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
    ]

    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='routes',
        limit_choices_to={'role': 'company'},
        verbose_name='Компанія'
    )
    carrier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_routes',
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    origin_city = models.CharField(
        max_length=255,
        verbose_name='Місто відправлення'
    )
    origin_country = models.CharField(
        max_length=100,
        verbose_name='Країна відправлення'
    )
    origin_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Широта відправлення'
    )
    origin_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Довгота відправлення'
    )
    destination_city = models.CharField(
        max_length=255,
        verbose_name='Місто призначення'
    )
    destination_country = models.CharField(
        max_length=100,
        verbose_name='Країна призначення'
    )
    destination_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Широта призначення'
    )
    destination_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Довгота призначення'
    )
    cargo_type = models.CharField(
        max_length=255,
        verbose_name='Тип вантажу'
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Вага (кг)'
    )
    volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Об\'єм (м³)'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Ціна'
    )
    pickup_date = models.DateTimeField(
        verbose_name='Дата забору'
    )
    delivery_date = models.DateTimeField(
        verbose_name='Дата доставки'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Оновлено'
    )

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршрути'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.origin_city} → {self.destination_city} ({self.status})"


class Bid(models.Model):
    """Ставка перевізника на маршрут"""
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name='Маршрут'
    )
    carrier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bids',
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    proposed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Запропонована ціна'
    )
    estimated_delivery = models.DateTimeField(
        verbose_name='Орієнтовна доставка'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Повідомлення'
    )
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='Прийнято'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    class Meta:
        verbose_name = 'Ставка'
        verbose_name_plural = 'Ставки'
        ordering = ['-created_at']
        unique_together = ['route', 'carrier']

    def __str__(self):
        return f"Ставка від {self.carrier.username} на маршрут {self.route}"


class Tracking(models.Model):
    """Відстеження вантажу"""
    route = models.OneToOneField(
        Route,
        on_delete=models.CASCADE,
        related_name='tracking',
        verbose_name='Маршрут'
    )
    current_location = models.CharField(
        max_length=255,
        verbose_name='Поточна локація',
        default=''
    )
    current_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Поточна широта'
    )
    current_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Поточна довгота'
    )
    progress_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Прогрес (%)'
    )
    last_update = models.DateTimeField(
        auto_now=True,
        verbose_name='Останнє оновлення'
    )

    class Meta:
        verbose_name = 'Відстеження'
        verbose_name_plural = 'Відстеження'
        ordering = ['-last_update']

    def __str__(self):
        return f"Відстеження {self.route} - {self.progress_percent}%"


class Message(models.Model):
    """Повідомлення між компанією та перевізником"""
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Маршрут'
    )
    sender = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Відправник'
    )
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Отримувач'
    )
    content = models.TextField(
        verbose_name='Текст повідомлення'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    class Meta:
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.content[:50]}"


class Notification(models.Model):
    """Сповіщення для користувачів"""
    NOTIFICATION_TYPES = [
        ('new_bid', 'Нова ставка'),
        ('bid_accepted', 'Вашу ставку прийнято'),
        ('bid_rejected', 'Вашу ставку відхилено'),
        ('new_message', 'Нове повідомлення'),
        ('route_assigned', 'Вам призначено маршрут'),
        ('route_completed', 'Маршрут завершено'),
        ('tracking_updated', 'Оновлено відстеження'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Користувач'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Тип сповіщення'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок'
    )
    message = models.TextField(
        verbose_name='Текст сповіщення'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Маршрут'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    class Meta:
        verbose_name = 'Сповіщення'
        verbose_name_plural = 'Сповіщення'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
