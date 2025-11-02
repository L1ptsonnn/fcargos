from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import User, CompanyProfile, CarrierProfile


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логін',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Увійти', css_class='btn btn-primary w-100')
        )


class CompanyRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-enhanced'})
    )
    company_name = forms.CharField(
        label='Назва компанії',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-enhanced'})
    )
    address = forms.CharField(
        label='Адреса',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-enhanced',
            'rows': 2,
            'id': 'address_field_company',
            'placeholder': 'Вкажіть адресу на карті',
            'readonly': True
        })
    )
    address_lat = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'address_lat_company'})
    )
    address_lng = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'address_lng_company'})
    )
    tax_id = forms.CharField(
        label='Податковий номер',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-enhanced'})
    )
    description = forms.CharField(
        label='Опис',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control form-control-enhanced', 'rows': 5})
    )
    logo = forms.ImageField(
        label='Логотип',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 'address', 'address_lat', 'address_lng', 'tax_id', 'description', 'logo')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-enhanced'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control form-control-enhanced'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control form-control-enhanced'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
            'company_name',
            Field('address'),
            Field('address_lat'),
            Field('address_lng'),
            'tax_id',
            'description',
            'logo',
            Submit('submit', 'Зареєструватися', css_class='btn btn-success w-100 mt-3')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'company'
        user.company_name = self.cleaned_data['company_name']
        if commit:
            user.save()
        return user


class CarrierRegistrationForm(UserCreationForm):
    # Популярні моделі вантажівок
    POPULAR_VEHICLE_MODELS = [
        ('', 'Оберіть модель або введіть свою'),
        ('Mercedes-Benz Actros', 'Mercedes-Benz Actros'),
        ('Volvo FH', 'Volvo FH'),
        ('Scania R-series', 'Scania R-series'),
        ('MAN TGX', 'MAN TGX'),
        ('DAF XF', 'DAF XF'),
        ('Iveco Stralis', 'Iveco Stralis'),
        ('Renault T', 'Renault T'),
        ('Mercedes-Benz Atego', 'Mercedes-Benz Atego'),
        ('Volvo FL', 'Volvo FL'),
        ('MAN TGL', 'MAN TGL'),
        ('Ford Transit', 'Ford Transit'),
        ('Mercedes Sprinter', 'Mercedes Sprinter'),
        ('Fiat Ducato', 'Fiat Ducato'),
        ('Renault Master', 'Renault Master'),
        ('ГАЗель', 'ГАЗель'),
        ('ЗІЛ', 'ЗІЛ'),
        ('КрАЗ', 'КрАЗ'),
        ('КАМАЗ', 'КАМАЗ'),
        ('Інша модель', 'Інша модель'),
    ]
    
    # Коди країн для номерів
    LICENSE_COUNTRIES = [
        ('UA', 'Україна (UA)'),
        ('PL', 'Польща (PL)'),
        ('DE', 'Німеччина (D)'),
        ('FR', 'Франція (F)'),
        ('IT', 'Італія (I)'),
        ('ES', 'Іспанія (E)'),
        ('NL', 'Нідерланди (NL)'),
        ('BE', 'Бельгія (B)'),
        ('AT', 'Австрія (A)'),
        ('CZ', 'Чехія (CZ)'),
        ('SK', 'Словаччина (SK)'),
        ('HU', 'Угорщина (H)'),
        ('RO', 'Румунія (RO)'),
        ('BG', 'Болгарія (BG)'),
        ('TR', 'Туреччина (TR)'),
    ]
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-enhanced'})
    )
    vehicle_type = forms.ChoiceField(
        label='Тип транспорту',
        choices=[
            ('', 'Оберіть тип'),
            ('Вантажівка', 'Вантажівка'),
            ('Фургон', 'Фургон'),
            ('Рефрижератор', 'Рефрижератор'),
            ('Цистерна', 'Цистерна'),
            ('Автопоїзд', 'Автопоїзд'),
            ('Тягач', 'Тягач'),
            ('Інший', 'Інший'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-enhanced'})
    )
    vehicle_model = forms.ChoiceField(
        label='Модель машини',
        choices=POPULAR_VEHICLE_MODELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-enhanced', 'id': 'vehicle_model_select'})
    )
    vehicle_model_custom = forms.CharField(
        label='Ваша модель',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-enhanced',
            'id': 'vehicle_model_custom',
            'style': 'display: none;',
            'placeholder': 'Введіть модель вашого транспорту'
        })
    )
    address = forms.CharField(
        label='Адреса',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-enhanced',
            'rows': 2,
            'id': 'address_field',
            'placeholder': 'Вкажіть адресу на карті',
            'readonly': True
        })
    )
    address_lat = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'address_lat'})
    )
    address_lng = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'address_lng'})
    )
    experience_years = forms.IntegerField(
        label='Досвід (років)',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-enhanced'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-enhanced'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control form-control-enhanced', 'id': 'id_password1'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control form-control-enhanced', 'id': 'id_password2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
            Field('vehicle_type'),
            Field('vehicle_model'),
            Field('vehicle_model_custom'),
            Field('address'),
            Field('address_lat'),
            Field('address_lng'),
            Field('experience_years'),
            Submit('submit', 'Зареєструватися', css_class='btn btn-success w-100 mt-3')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        vehicle_model = cleaned_data.get('vehicle_model')
        vehicle_model_custom = cleaned_data.get('vehicle_model_custom')
        
        # Якщо обрано "Інша модель" або порожньо, використовуємо кастомну
        if vehicle_model == 'Інша модель' or not vehicle_model:
            if not vehicle_model_custom:
                raise forms.ValidationError('Будь ласка, введіть модель вашого транспорту.')
            cleaned_data['vehicle_model'] = vehicle_model_custom
        elif vehicle_model_custom and vehicle_model != 'Інша модель':
            # Якщо обрано зі списку, ігноруємо кастомну
            cleaned_data['vehicle_model_custom'] = ''
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'carrier'
        if commit:
            user.save()
            # Створюємо профіль перевізника
            vehicle_model = self.cleaned_data['vehicle_model']
            if not vehicle_model:
                vehicle_model = self.cleaned_data.get('vehicle_model_custom', '')
            
            CarrierProfile.objects.create(
                user=user,
                license_number=f"CARRIER-{user.id}-{user.username[:3].upper()}",  # Автоматично генеруємо номер
                license_country='UA',  # За замовчуванням
                vehicle_type=self.cleaned_data['vehicle_type'],
                vehicle_model=vehicle_model,
                address=self.cleaned_data.get('address', ''),
                address_lat=self.cleaned_data.get('address_lat'),
                address_lng=self.cleaned_data.get('address_lng'),
                experience_years=self.cleaned_data['experience_years']
            )
        return user

