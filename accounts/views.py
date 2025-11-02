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
            form.save()  # Форма вже створює профіль
            messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
            return redirect('login')
    else:
        form = CarrierRegistrationForm()
    
    return render(request, 'accounts/register_carrier.html', {'form': form})


def register_view(request):
    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    from logistics.models import Route, Bid, Tracking
    from django.db.models import Count, Sum, Avg
    from django.forms import ModelForm
    
    context = {}
    
    if request.user.role == 'company':
        try:
            context['profile'] = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            context['profile'] = None
        
        # Статистика для компанії
        routes = Route.objects.filter(company=request.user)
        context['total_routes'] = routes.count()
        context['pending_routes'] = routes.filter(status='pending').count()
        context['in_transit_routes'] = routes.filter(status='in_transit').count()
        context['delivered_routes'] = routes.filter(status='delivered').count()
        context['total_spent'] = routes.filter(status__in=['in_transit', 'delivered']).aggregate(Sum('price'))['price__sum'] or 0
        context['recent_routes'] = routes.order_by('-created_at')[:5]
        context['all_routes'] = routes
        
    elif request.user.role == 'carrier':
        try:
            context['profile'] = request.user.carrier_profile
        except CarrierProfile.DoesNotExist:
            context['profile'] = None
        
        # Статистика для перевізника
        bids = Bid.objects.filter(carrier=request.user)
        routes = Route.objects.filter(carrier=request.user)
        context['total_bids'] = bids.count()
        context['accepted_bids'] = bids.filter(is_accepted=True).count()
        context['completed_routes'] = routes.filter(status='delivered').count()
        context['active_routes'] = routes.filter(status='in_transit').count()
        context['total_earned'] = routes.filter(status='delivered').aggregate(Sum('price'))['price__sum'] or 0
        context['average_price'] = routes.filter(status='delivered').aggregate(Avg('price'))['price__avg'] or 0
        context['recent_bids'] = bids.order_by('-created_at')[:5]
        context['my_routes'] = routes.order_by('-created_at')[:5]
    
    # Перевірка чи користувач адмін
    context['is_admin'] = request.user.is_staff
    
    return render(request, 'accounts/profile.html', context)
