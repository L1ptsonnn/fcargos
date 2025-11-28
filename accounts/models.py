from django.contrib.auth.models import AbstractUser
from django.db import models


# Кастомна модель користувача, що розширює Django AbstractUser
# Додаємо власні поля (роль, назва компанії тощо)
class User(AbstractUser):
    """Кастомний користувач із підтримкою ролей"""
    
    # Доступні ролі користувача: компанія або перевізник
    ROLE_CHOICES = [
        ('company', 'Компанія'),   # Компанія створює маршрути
        ('carrier', 'Перевізник'),  # Перевізник робить ставки
    ]
    
    # Поле ролі визначає тип користувача
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name='Роль'
    )
    
    # Номер телефону (опційне поле, наразі не використовується у формі)
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    
    # Назва компанії зберігається лише для ролі company
    company_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Назва компанії'
    )
    
    # Час створення користувача
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )
    
    # Час останнього оновлення профілю
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Оновлено'
    )

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        ordering = ['-created_at']  # Спочатку нові користувачі

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Профіль компанії: додаткові дані для користувачів-компаній
# Зв'язок один-до-одного з User (1 користувач = 1 профіль)
class CompanyProfile(models.Model):
    """Модель профілю компанії"""
    
    # Посилання на користувача; при видаленні користувача видаляємо профіль
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # Видаляємо профіль разом із користувачем
        related_name='company_profile'  # Доступ до профілю user.company_profile
    )
    
    # Юридична адреса компанії
    address = models.TextField(verbose_name='Адреса')
    
    # Широта адреси (для карти)
    address_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Широта'
    )
    
    # Довгота адреси (для карти)
    address_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Довгота'
    )
    
    # Податковий номер (унікальний для кожної компанії)
    tax_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Податковий номер'
    )
    
    # Опис компанії (необов'язковий)
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
    
    # Логотип (файл потрапляє в media/companies/logos/)
    logo = models.ImageField(
        upload_to='companies/logos/',
        blank=True,
        null=True,
        verbose_name='Логотип'
    )

    class Meta:
        verbose_name = 'Профіль компанії'
        verbose_name_plural = 'Профілі компаній'
        ordering = ['user__company_name']

    def __str__(self):
        return f"Профіль {self.user.company_name}"


# Профіль перевізника: додаткова інформація для ролі carrier
# Також зв'язок один-до-одного з користувачем
class CarrierProfile(models.Model):
    """Модель профілю перевізника"""
    
    # Долучаємо користувача і видаляємо профіль при видаленні користувача
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # Каскадне видалення
        related_name='carrier_profile'  # доступ через user.carrier_profile
    )
    
    # Ліцензія/реєстраційний номер транспорту (унікальний)
    license_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Номер ліцензії'
    )
    
    # Код країни номера (за замовчуванням UA)
    license_country = models.CharField(
        max_length=10,
        default='UA',
        verbose_name='Країна номера',
        help_text='Код країни для номерного знаку'
    )
    
    # Тип транспорту (вантажівка, бус тощо)
    vehicle_type = models.CharField(
        max_length=100,
        verbose_name='Тип транспорту'
    )
    
    # Модель авто (наприклад, Mercedes Actros)
    vehicle_model = models.CharField(
        max_length=150,
        verbose_name='Модель машини'
    )
    
    # Адреса (можна залишити порожньою)
    address = models.TextField(
        blank=True,
        verbose_name='Адреса'
    )
    
    # Широта адреси
    address_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Широта адреси'
    )
    
    # Довгота адреси
    address_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Довгота адреси'
    )
    
    # Стаж у роках
    experience_years = models.IntegerField(
        default=0,
        verbose_name='Досвід (років)'
    )
    
    # Опис досвіду та послуг
    description = models.TextField(
        blank=True,
        verbose_name='Опис',
        help_text='Опис вашого досвіду та послуг'
    )
    
    # Середній рейтинг (0.00–5.00), обчислюється автоматично
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Рейтинг'
    )

    class Meta:
        verbose_name = 'Профіль перевізника'
        verbose_name_plural = 'Профілі перевізників'
        # Спочатку за рейтингом (спадаючий), потім за логіном
        ordering = ['-rating', 'user__username']

    def __str__(self):
        return f"Профіль перевізника {self.user.username}"
