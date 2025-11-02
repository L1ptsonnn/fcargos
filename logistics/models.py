from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User


# Route model - represents a delivery route from origin to destination
# Created by companies, carriers can bid on it, after acceptance carrier delivers it
class Route(models.Model):
    """Delivery route model"""
    
    # Route status choices - possible states of a route
    STATUS_CHOICES = [
        ('pending', 'Очікує'),       # Waiting for bids (no carrier assigned)
        ('in_transit', 'В дорозі'),  # Carrier is delivering (cargo is moving)
        ('delivered', 'Доставлено'), # Route completed successfully
        ('cancelled', 'Скасовано'),  # Route was cancelled
        ('expired', 'Просрочений'),  # No bid accepted before pickup_date
    ]

    # Company that created this route (owner)
    # CASCADE: if company is deleted, all their routes are deleted
    # limit_choices_to: only users with role='company' can be selected
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='routes',  # Access via company.routes.all()
        limit_choices_to={'role': 'company'},
        verbose_name='Компанія'
    )
    
    # Carrier assigned to this route (optional - only after bid acceptance)
    # SET_NULL: if carrier is deleted, route.carrier becomes None (route is not deleted)
    # limit_choices_to: only users with role='carrier' can be selected
    carrier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_routes',  # Access via carrier.assigned_routes.all()
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    # Origin location (where cargo is picked up)
    origin_city = models.CharField(
        max_length=255,
        verbose_name='Місто відправлення'
    )
    origin_country = models.CharField(
        max_length=100,
        verbose_name='Країна відправлення'
    )
    # Latitude/longitude for map display (from map click or geocoding)
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
    
    # Destination location (where cargo is delivered)
    destination_city = models.CharField(
        max_length=255,
        verbose_name='Місто призначення'
    )
    destination_country = models.CharField(
        max_length=100,
        verbose_name='Країна призначення'
    )
    # Latitude/longitude for map display (from map click or geocoding)
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
    
    # Cargo information
    cargo_type = models.CharField(
        max_length=255,
        verbose_name='Тип вантажу'
    )
    # Weight in kilograms (must be >= 0)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Вага (кг)'
    )
    # Volume in cubic meters (must be >= 0)
    volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Об\'єм (м³)'
    )
    # Price in UAH (must be >= 0)
    # This can be updated when bid is accepted (to bid.proposed_price)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Ціна'
    )
    
    # Dates
    pickup_date = models.DateTimeField(
        verbose_name='Дата забору'
    )
    delivery_date = models.DateTimeField(
        verbose_name='Дата доставки'
    )
    
    # Route status (pending by default)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    # Optional description
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,  # Set when object is created
        verbose_name='Створено'
    )
    updated_at = models.DateTimeField(
        auto_now=True,  # Updated every time object is saved
        verbose_name='Оновлено'
    )

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршрути'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.origin_city} → {self.destination_city} ({self.status})"


# Bid model - represents a carrier's offer/price for a route
# Multiple carriers can bid on same route, but company accepts only one
class Bid(models.Model):
    """Carrier bid on route"""
    
    # Route this bid is for
    # CASCADE: if route is deleted, all bids are deleted
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='bids',  # Access via route.bids.all()
        verbose_name='Маршрут'
    )
    
    # Carrier who made this bid
    # CASCADE: if carrier is deleted, all their bids are deleted
    carrier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bids',  # Access via carrier.bids.all()
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    
    # Price proposed by carrier (can be different from route.price)
    proposed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Запропонована ціна'
    )
    
    # When carrier estimates delivery will be completed
    estimated_delivery = models.DateTimeField(
        verbose_name='Орієнтовна доставка'
    )
    
    # Optional message from carrier to company
    message = models.TextField(
        blank=True,
        verbose_name='Повідомлення'
    )
    
    # Whether company accepted this bid
    # Only one bid per route can have is_accepted=True
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='Прийнято'
    )
    
    # When bid was created
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    class Meta:
        verbose_name = 'Ставка'
        verbose_name_plural = 'Ставки'
        ordering = ['-created_at']  # Newest bids first
        # One carrier can only bid once per route (unique constraint)
        unique_together = ['route', 'carrier']

    def __str__(self):
        return f"Ставка від {self.carrier.username} на маршрут {self.route}"


# Tracking model - tracks cargo location and progress during delivery
# One-to-one with Route (one route = one tracking object)
class Tracking(models.Model):
    """Cargo tracking model"""
    
    # Route being tracked
    # OneToOne: one route has exactly one tracking object
    route = models.OneToOneField(
        Route,
        on_delete=models.CASCADE,  # If route deleted, tracking deleted
        related_name='tracking',  # Access via route.tracking
        verbose_name='Маршрут'
    )
    
    # Current location of cargo (text description)
    current_location = models.CharField(
        max_length=255,
        verbose_name='Поточна локація',
        default=''
    )
    
    # Current coordinates (calculated from progress_percent or set manually)
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
    
    # Progress percentage (0-100%)
    # 0% = at origin, 100% = at destination
    # Automatically calculated based on time or manually updated by carrier
    progress_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Прогрес (%)'
    )
    
    # When tracking was last updated
    last_update = models.DateTimeField(
        auto_now=True,  # Updated every time object is saved
        verbose_name='Останнє оновлення'
    )

    class Meta:
        verbose_name = 'Відстеження'
        verbose_name_plural = 'Відстеження'
        ordering = ['-last_update']

    def __str__(self):
        return f"Відстеження {self.route} - {self.progress_percent}%"


# Message model - chat messages between company and carrier about a route
# All messages are related to a specific route
class Message(models.Model):
    """Message between company and carrier"""
    
    # Route this message is about
    # CASCADE: if route deleted, all messages are deleted
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='messages',  # Access via route.messages.all()
        verbose_name='Маршрут'
    )
    
    # User who sent the message (can be company or carrier)
    sender = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_messages',  # Access via user.sent_messages.all()
        verbose_name='Відправник'
    )
    
    # User who receives the message (the other party - company or carrier)
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='received_messages',  # Access via user.received_messages.all()
        verbose_name='Отримувач'
    )
    
    # Message text content
    content = models.TextField(
        verbose_name='Текст повідомлення'
    )
    
    # Whether recipient has read the message
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    
    # When message was sent
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


# Notification model - in-app notifications for users
# Users get notifications about bids, messages, route updates, etc.
class Notification(models.Model):
    """User notification model"""
    
    # Types of notifications that can be created
    NOTIFICATION_TYPES = [
        ('new_bid', 'Нова ставка'),                    # New bid on route (company gets)
        ('bid_accepted', 'Вашу ставку прийнято'),      # Bid was accepted (carrier gets)
        ('bid_rejected', 'Вашу ставку відхилено'),    # Bid was rejected (carrier gets)
        ('new_message', 'Нове повідомлення'),         # New message received
        ('route_assigned', 'Вам призначено маршрут'), # Route assigned to carrier
        ('route_completed', 'Маршрут завершено'),     # Route was completed
        ('tracking_updated', 'Оновлено відстеження'), # Tracking was updated
        ('route_expired', 'Маршрут просрочений'),     # Route expired (company gets)
    ]
    
    # User who receives this notification
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',  # Access via user.notifications.all()
        verbose_name='Користувач'
    )
    
    # Type of notification (from NOTIFICATION_TYPES)
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Тип сповіщення'
    )
    
    # Notification title
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок'
    )
    
    # Notification message/content
    message = models.TextField(
        verbose_name='Текст сповіщення'
    )
    
    # Related route (optional - not all notifications are route-related)
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',  # Access via route.notifications.all()
        verbose_name='Маршрут'
    )
    
    # Whether user has read this notification
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    
    # When notification was created
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


class Rating(models.Model):
    """Оцінка перевізника від компанії"""
    carrier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_received',
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_given',
        limit_choices_to={'role': 'company'},
        verbose_name='Компанія'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True,
        verbose_name='Маршрут'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оцінка',
        help_text='Оцінка від 1 до 5'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Коментар'
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
        verbose_name = 'Оцінка'
        verbose_name_plural = 'Оцінки'
        unique_together = ('carrier', 'company', 'route')  # Одна оцінка від компанії для маршруту
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company.username} → {self.carrier.username}: {self.rating}/5"

    # Override save() to automatically update carrier's average rating
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update carrier's average rating after saving this rating
        self.update_carrier_rating()

    # Override delete() to update carrier's rating after deletion
    def delete(self, *args, **kwargs):
        carrier = self.carrier  # Save carrier reference before deletion
        super().delete(*args, **kwargs)
        # Update rating after deletion (recalculate average)
        self._update_carrier_rating_for(carrier)

    # Method to update carrier's average rating
    def update_carrier_rating(self):
        """Update carrier's average rating"""
        from accounts.models import CarrierProfile
        from django.db.models import Avg
        try:
            carrier_profile = CarrierProfile.objects.get(user=self.carrier)
            # Get all ratings for this carrier
            ratings = Rating.objects.filter(carrier=self.carrier)
            if ratings.exists():
                # Calculate average rating
                avg_rating = ratings.aggregate(avg=Avg('rating'))['avg']
                carrier_profile.rating = round(avg_rating, 2)  # Round to 2 decimal places
            else:
                # No ratings - set to 0
                carrier_profile.rating = 0.00
            carrier_profile.save()
        except CarrierProfile.DoesNotExist:
            pass  # Carrier profile doesn't exist - skip

    # Static method to update rating for a specific carrier
    @staticmethod
    def _update_carrier_rating_for(carrier):
        """Update rating for specific carrier"""
        from accounts.models import CarrierProfile
        from django.db.models import Avg
        try:
            carrier_profile = CarrierProfile.objects.get(user=carrier)
            ratings = Rating.objects.filter(carrier=carrier)
            if ratings.exists():
                avg_rating = ratings.aggregate(avg=Avg('rating'))['avg']
                carrier_profile.rating = round(avg_rating, 2)
            else:
                carrier_profile.rating = 0.00
            carrier_profile.save()
        except CarrierProfile.DoesNotExist:
            pass
