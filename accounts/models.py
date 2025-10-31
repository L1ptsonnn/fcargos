from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомна модель користувача з ролями"""
    ROLE_CHOICES = [
        ('company', 'Компанія'),
        ('carrier', 'Перевізник'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name='Роль'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Назва компанії'
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
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class CompanyProfile(models.Model):
    """Профіль компанії"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='company_profile'
    )
    address = models.TextField(verbose_name='Адреса')
    tax_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Податковий номер'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
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


class CarrierProfile(models.Model):
    """Профіль перевізника"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='carrier_profile'
    )
    license_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Номер ліцензії'
    )
    vehicle_type = models.CharField(
        max_length=100,
        verbose_name='Тип транспорту'
    )
    experience_years = models.IntegerField(
        default=0,
        verbose_name='Досвід (років)'
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Рейтинг'
    )

    class Meta:
        verbose_name = 'Профіль перевізника'
        verbose_name_plural = 'Профілі перевізників'
        ordering = ['-rating', 'user__username']

    def __str__(self):
        return f"Профіль перевізника {self.user.username}"
