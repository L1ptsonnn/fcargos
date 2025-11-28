from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CompanyProfile, CarrierProfile

# User admin, allows to edit user information
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'company_name', 'phone', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'company_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Додаткова інформація', {
            'fields': ('role', 'phone', 'company_name')
        }),
    )

# Company profile admin, allows to edit company profile information
@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tax_id', 'address')
    search_fields = ('user__username', 'tax_id', 'address')
    list_filter = ('user__created_at',)

# Carrier profile admin, allows to edit carrier profile information
@admin.register(CarrierProfile)
class CarrierProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'vehicle_type', 'experience_years', 'rating')
    search_fields = ('user__username', 'license_number')
    list_filter = ('vehicle_type', 'rating')
