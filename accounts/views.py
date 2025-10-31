from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, CompanyProfile, CarrierProfile
from .forms import LoginForm, CompanyRegistrationForm, CarrierRegistrationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Ласкаво просимо, {user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Невірний логін або пароль')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def register_company(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            CompanyProfile.objects.create(
                user=user,
                address=form.cleaned_data['address'],
                tax_id=form.cleaned_data['tax_id'],
                description=form.cleaned_data.get('description', ''),
                logo=form.cleaned_data.get('logo')
            )
            messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
            return redirect('login')
    else:
        form = CompanyRegistrationForm()
    
    return render(request, 'accounts/register_company.html', {'form': form})


def register_carrier(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CarrierRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            CarrierProfile.objects.create(
                user=user,
                license_number=form.cleaned_data['license_number'],
                vehicle_type=form.cleaned_data['vehicle_type'],
                experience_years=form.cleaned_data.get('experience_years', 0)
            )
            messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
            return redirect('login')
    else:
        form = CarrierRegistrationForm()
    
    return render(request, 'accounts/register_carrier.html', {'form': form})


def register_view(request):
    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    context = {}
    if request.user.role == 'company':
        try:
            context['profile'] = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            context['profile'] = None
    elif request.user.role == 'carrier':
        try:
            context['profile'] = request.user.carrier_profile
        except CarrierProfile.DoesNotExist:
            context['profile'] = None
    return render(request, 'accounts/profile.html', context)
