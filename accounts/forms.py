from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
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
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Увійти', css_class='btn btn-primary w-100')
        )


class CompanyRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    company_name = forms.CharField(
        label='Назва компанії',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        label='Адреса',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    tax_id = forms.CharField(
        label='Податковий номер',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        label='Опис',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )
    logo = forms.ImageField(
        label='Логотип',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 'phone')
    
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
            'phone',
            'address',
            'tax_id',
            'description',
            'logo',
            Submit('submit', 'Зареєструватися', css_class='btn btn-success w-100 mt-3')
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'company'
        user.company_name = self.cleaned_data['company_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user


class CarrierRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    license_number = forms.CharField(
        label='Номер ліцензії',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    vehicle_type = forms.CharField(
        label='Тип транспорту',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    experience_years = forms.IntegerField(
        label='Досвід (років)',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone')
    
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
            'phone',
            'license_number',
            'vehicle_type',
            'experience_years',
            Submit('submit', 'Зареєструватися', css_class='btn btn-success w-100 mt-3')
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'carrier'
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

