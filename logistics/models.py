from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User


# Модель маршруту: шлях доставки від точки А до Б
# Створюють компанії, перевізники подають ставки, після прийняття виконують доставку
class Route(models.Model):
    """Delivery route model"""
    
    # Перелік статусів маршруту
    STATUS_CHOICES = [
        ('pending', 'Очікує'),       # ставки очікуються, перевізника нема
        ('in_transit', 'В дорозі'),  # вантаж у русі
        ('delivered', 'Доставлено'), # маршрут завершено
        ('cancelled', 'Скасовано'),  # маршрут скасовано
        ('expired', 'Просрочений'),  # не прийнято ставку до pickup_date
    ]

    # Компанія-власник маршруту; CASCADE — видаляємо маршрути разом із компанією
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='routes',  # доступ через company.routes.all()
        limit_choices_to={'role': 'company'},
        verbose_name='Компанія'
    )
    
    # Перевізник призначається після прийняття ставки; при видаленні — SET_NULL
    carrier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_routes',  # доступ через carrier.assigned_routes.all()
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    # Локація відправлення
    origin_city = models.CharField(
        max_length=255,
        verbose_name='Місто відправлення'
    )
    origin_country = models.CharField(
        max_length=100,
        verbose_name='Країна відправлення'
    )
    # Координати широти/довготи (для карти)
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
    
    # Локація призначення
    destination_city = models.CharField(
        max_length=255,
        verbose_name='Місто призначення'
    )
    destination_country = models.CharField(
        max_length=100,
        verbose_name='Країна призначення'
    )
    # Координати призначення
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
    
    # Опис вантажу
    cargo_type = models.CharField(
        max_length=255,
        verbose_name='Тип вантажу'
    )
    # Вага (кг), не менше нуля
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Вага (кг)'
    )
    # Об'єм (м³), не менше нуля
    volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Об\'єм (м³)'
    )
    # Ціна (грн), може оновлюватися до запропонованої ставки
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Ціна'
    )
    
    # Дати
    pickup_date = models.DateTimeField(
        verbose_name='Дата забору'
    )
    delivery_date = models.DateTimeField(
        verbose_name='Дата доставки'
    )
    
    # Статус маршруту (за замовчуванням pending)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    # Необов'язковий опис
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
    
    # Мітки часу
    created_at = models.DateTimeField(
        auto_now_add=True,  # при створенні
        verbose_name='Створено'
    )
    updated_at = models.DateTimeField(
        auto_now=True,  # оновлюється при збереженні
        verbose_name='Оновлено'
    )

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршрути'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.origin_city} → {self.destination_city} ({self.status})"


# Модель ставки перевізника; компанія обирає максимум одну ставку на маршрут
class Bid(models.Model):
    """Carrier bid on route"""
    
    # Маршрут, до якого належить ставка (при видаленні маршруту видаляються й ставки)
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='bids',  # доступ через route.bids.all()
        verbose_name='Маршрут'
    )
    
    # Перевізник, що зробив ставку (при видаленні видаляємо й ставки)
    carrier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bids',  # доступ через carrier.bids.all()
        limit_choices_to={'role': 'carrier'},
        verbose_name='Перевізник'
    )
    
    # Запропонована ціна (може відрізнятися від базової)
    proposed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Запропонована ціна'
    )
    
    # Орієнтовний час доставки
    estimated_delivery = models.DateTimeField(
        verbose_name='Орієнтовна доставка'
    )
    
    # Додаткове повідомлення від перевізника
    message = models.TextField(
        blank=True,
        verbose_name='Повідомлення'
    )
    
    # Прапорець прийняття; лише одна ставка може бути прийнята
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='Прийнято'
    )
    
    # Час створення ставки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    class Meta:
        verbose_name = 'Ставка'
        verbose_name_plural = 'Ставки'
        ordering = ['-created_at']  # спочатку нові
        # Один перевізник може зробити лише одну ставку на маршрут
        unique_together = ['route', 'carrier']

    def __str__(self):
        return f"Ставка від {self.carrier.username} на маршрут {self.route}"


# Відстеження маршруту (one-to-one з Route)
class Tracking(models.Model):
    """Cargo tracking model"""
    
    # Маршрут, що відстежується
    route = models.OneToOneField(
        Route,
        on_delete=models.CASCADE,  # видаляємо разом із маршрутом
        related_name='tracking',  # доступ через route.tracking
        verbose_name='Маршрут'
    )
    
    # Поточна текстова локація вантажу
    current_location = models.CharField(
        max_length=255,
        verbose_name='Поточна локація',
        default=''
    )
    
    # Поточні координати (розраховуються чи задаються вручну)
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
    
    # Прогрес у відсотках (0% — старт, 100% — призначення)
    # Може розраховуватись автоматично або вручну перевізником
    progress_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Прогрес (%)'
    )
    
    # Час останнього оновлення
    last_update = models.DateTimeField(
        auto_now=True,  # оновлюється при кожному save
        verbose_name='Останнє оновлення'
    )

    class Meta:
        verbose_name = 'Відстеження'
        verbose_name_plural = 'Відстеження'
        ordering = ['-last_update']

    def __str__(self):
        return f"Відстеження {self.route} - {self.progress_percent}%"


# Повідомлення між компанією та перевізником щодо маршруту
class Message(models.Model):
    """Message between company and carrier"""
    
    # Маршрут, до якого належить повідомлення (при видаленні зникає)
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='messages',  # доступ через route.messages.all()
        verbose_name='Маршрут'
    )
    
    # Відправник (компанія чи перевізник)
    sender = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_messages',  # доступ через user.sent_messages.all()
        verbose_name='Відправник'
    )
    
    # Отримувач (інша сторона)
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='received_messages',  # доступ через user.received_messages.all()
        verbose_name='Отримувач'
    )
    
    # Текст листування
    content = models.TextField(
        verbose_name='Текст повідомлення'
    )
    
    # Позначка про прочитання
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    
    # Час відправлення
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


# Сповіщення в застосунку: ставки, повідомлення, оновлення маршрутів тощо
class Notification(models.Model):
    """User notification model"""
    
    # Типи доступних сповіщень
    NOTIFICATION_TYPES = [
        ('new_bid', 'Нова ставка'),                    # ставок стало більше
        ('bid_accepted', 'Вашу ставку прийнято'),      # прийняли ставку
        ('bid_rejected', 'Вашу ставку відхилено'),    # відмовили у ставці
        ('new_message', 'Нове повідомлення'),         # новий чат
        ('route_assigned', 'Вам призначено маршрут'), # перевізника призначено
        ('route_completed', 'Маршрут завершено'),     # маршрут завершено
        ('tracking_updated', 'Оновлено відстеження'), # оновлено прогрес
        ('route_expired', 'Маршрут просрочений'),     # маршрут прострочений
    ]
    
    # Отримувач сповіщення
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',  # доступ через user.notifications.all()
        verbose_name='Користувач'
    )
    
    # Тип сповіщення
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Тип сповіщення'
    )
    
    # Заголовок
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок'
    )
    
    # Текст
    message = models.TextField(
        verbose_name='Текст сповіщення'
    )
    
    # Дотичний маршрут (може бути None)
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',  # доступ через route.notifications.all()
        verbose_name='Маршрут'
    )
    
    # Прапорець прочитано/непрочитано
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    
    # Час створення
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
        unique_together = ('carrier', 'company', 'route')  # одна оцінка від компанії для маршруту
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company.username} → {self.carrier.username}: {self.rating}/5"

    # Перевизначаємо save, щоб оновлювати середній рейтинг перевізника
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Оновлюємо середнє після збереження оцінки
        self.update_carrier_rating()

    # Аналогічно перевизначаємо delete для перерахунку рейтингу
    def delete(self, *args, **kwargs):
        carrier = self.carrier  # зберігаємо посилання до видалення
        super().delete(*args, **kwargs)
        # Після видалення перераховуємо рейтинг
        self._update_carrier_rating_for(carrier)

    # Метод перерахунку середнього рейтингу
    def update_carrier_rating(self):
        """Update carrier's average rating"""
        from accounts.models import CarrierProfile
        from django.db.models import Avg
        try:
            carrier_profile = CarrierProfile.objects.get(user=self.carrier)
            # Збираємо всі оцінки перевізника
            ratings = Rating.objects.filter(carrier=self.carrier)
            if ratings.exists():
                # Обчислюємо середнє
                avg_rating = ratings.aggregate(avg=Avg('rating'))['avg']
                carrier_profile.rating = round(avg_rating, 2)  # округлюємо до сотих
            else:
                # Якщо оцінок немає — записуємо 0
                carrier_profile.rating = 0.00
            carrier_profile.save()
        except CarrierProfile.DoesNotExist:
            pass  # профіль відсутній — пропускаємо

    # Статичний метод для окремого перевізника
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
