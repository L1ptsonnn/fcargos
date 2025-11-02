from django.contrib.auth.models import AbstractUser
from django.db import models


# Custom user model that extends Django's AbstractUser
# This allows us to add custom fields like role, company_name, etc.
class User(AbstractUser):
    """Custom user model with roles"""
    
    # Role choices for the user - can be either company or carrier
    ROLE_CHOICES = [
        ('company', 'Компанія'),   # Company that creates routes
        ('carrier', 'Перевізник'),  # Carrier that makes bids on routes
    ]
    
    # User role field - determines if user is company or carrier
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name='Роль'
    )
    
    # Phone number field (currently optional, not used in registration)
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    
    # Company name - only used if role is 'company'
    company_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Назва компанії'
    )
    
    # Timestamp when user was created
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )
    
    # Timestamp when user was last updated
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Оновлено'
    )

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        ordering = ['-created_at']  # Newest users first

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Company profile model - stores additional information for company users
# One-to-one relationship with User model (one user = one company profile)
class CompanyProfile(models.Model):
    """Company profile model"""
    
    # Link to the User model - OneToOne means one user has one company profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # If user is deleted, profile is also deleted
        related_name='company_profile'  # Access via user.company_profile
    )
    
    # Company address (text description)
    address = models.TextField(verbose_name='Адреса')
    
    # Latitude coordinate of company address (for map display)
    address_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Широта'
    )
    
    # Longitude coordinate of company address (for map display)
    address_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Довгота'
    )
    
    # Tax identification number (unique - each company has unique tax ID)
    tax_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Податковий номер'
    )
    
    # Company description (optional text field)
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
    
    # Company logo image (uploaded to media/companies/logos/)
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


# Carrier profile model - stores additional information for carrier users
# One-to-one relationship with User model (one user = one carrier profile)
class CarrierProfile(models.Model):
    """Carrier profile model"""
    
    # Link to the User model - OneToOne means one user has one carrier profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # If user is deleted, profile is also deleted
        related_name='carrier_profile'  # Access via user.carrier_profile
    )
    
    # License/registration number for the vehicle (unique identifier)
    license_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Номер ліцензії'
    )
    
    # Country code for the license plate (default is Ukraine - UA)
    license_country = models.CharField(
        max_length=10,
        default='UA',
        verbose_name='Країна номера',
        help_text='Код країни для номерного знаку'
    )
    
    # Type of vehicle (e.g., "Вантажівка", "Легкова")
    vehicle_type = models.CharField(
        max_length=100,
        verbose_name='Тип транспорту'
    )
    
    # Vehicle model (e.g., "Mercedes Actros", "Volvo FH")
    vehicle_model = models.CharField(
        max_length=150,
        verbose_name='Модель машини'
    )
    
    # Carrier address (text description)
    address = models.TextField(
        blank=True,
        verbose_name='Адреса'
    )
    
    # Latitude coordinate of carrier address (for map display)
    address_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Широта адреси'
    )
    
    # Longitude coordinate of carrier address (for map display)
    address_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Довгота адреси'
    )
    
    # Years of experience in logistics
    experience_years = models.IntegerField(
        default=0,
        verbose_name='Досвід (років)'
    )
    
    # Carrier description (optional text field)
    description = models.TextField(
        blank=True,
        verbose_name='Опис',
        help_text='Опис вашого досвіду та послуг'
    )
    
    # Average rating from companies (calculated automatically from Rating model)
    # Range: 0.00 to 5.00
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Рейтинг'
    )

    class Meta:
        verbose_name = 'Профіль перевізника'
        verbose_name_plural = 'Профілі перевізників'
        # Order by rating (highest first), then by username
        ordering = ['-rating', 'user__username']

    def __str__(self):
        return f"Профіль перевізника {self.user.username}"
