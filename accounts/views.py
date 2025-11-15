from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import User, CompanyProfile, CarrierProfile
from .forms import LoginForm, CompanyRegistrationForm, CarrierRegistrationForm, CompanyProfileEditForm, CarrierProfileEditForm


# Login view - handles user authentication
# GET: Shows login form
# POST: Validates credentials and logs user in
def login_view(request):
    # If user is already logged in, redirect to home page
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('<script>window.location.href = "/";</script>')
        return redirect('home')
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'accounts/login_partial.html' if is_htmx else 'accounts/login.html'
    
    # If form was submitted (POST request)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Get username and password from form
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Authenticate user (check if credentials are correct)
            user = authenticate(request, username=username, password=password)
            if user:
                # Log user in (create session)
                login(request, user)
                messages.success(request, f'Ласкаво просимо, {user.username}!')
                if is_htmx:
                    return HttpResponse('<script>window.location.href = "/";</script>')
                return redirect('home')
            else:
                # Invalid credentials
                messages.error(request, 'Невірний логін або пароль')
    else:
        # GET request - show empty form
        form = LoginForm()
    
    # Render login template with form
    return render(request, template, {'form': form})


# Company registration view - handles company user registration
# GET: Shows registration form
# POST: Creates new company user and profile
def register_company(request):
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('<script>window.location.href = "/";</script>')
        return redirect('home')
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'accounts/register_company_partial.html' if is_htmx else 'accounts/register_company.html'
    
    # If form was submitted (POST request)
    if request.method == 'POST':
        # request.FILES is needed for file uploads (logo)
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = None
            try:
                # Save user (form.save() creates User with role='company')
                user = form.save()
                
                # Create company profile with additional information
                CompanyProfile.objects.create(
                    user=user,
                    address=form.cleaned_data.get('address', ''),
                    address_lat=form.cleaned_data.get('address_lat'),  # Latitude from map
                    address_lng=form.cleaned_data.get('address_lng'),  # Longitude from map
                    tax_id=form.cleaned_data['tax_id'],  # Tax identification number
                    description=form.cleaned_data.get('description', ''),  # Optional description
                    logo=form.cleaned_data.get('logo')  # Optional logo image
                )
                messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
                if is_htmx:
                    return HttpResponse('<script>window.location.href = "/accounts/login/";</script>')
                return redirect('login')
            except Exception as e:
                # Якщо виникла помилка при створенні профілю (наприклад, дублікат tax_id)
                # Видаляємо створеного користувача, щоб уникнути "сирого" запису
                if user and user.pk:
                    user.delete()
                # Повторно перевіряємо tax_id і додаємо помилку до форми
                if 'tax_id' in str(e).lower() or 'unique' in str(e).lower():
                    form.add_error('tax_id', 'Компанія з таким податковим номером вже зареєстрована.')
                else:
                    messages.error(request, f'Помилка при реєстрації: {str(e)}')
    else:
        # GET request - show empty form
        form = CompanyRegistrationForm()
    
    # Render registration template with form
    return render(request, template, {'form': form})


# Carrier registration view - handles carrier user registration
# GET: Shows registration form
# POST: Creates new carrier user and profile
def register_carrier(request):
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('<script>window.location.href = "/";</script>')
        return redirect('home')
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'accounts/register_carrier_partial.html' if is_htmx else 'accounts/register_carrier.html'
    
    # If form was submitted (POST request)
    if request.method == 'POST':
        form = CarrierRegistrationForm(request.POST)
        if form.is_valid():
            # form.save() creates both User and CarrierProfile automatically
            # (see CarrierRegistrationForm.save() method)
            form.save()
            messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
            if is_htmx:
                return HttpResponse('<script>window.location.href = "/accounts/login/";</script>')
            return redirect('login')
    else:
        # GET request - show empty form
        form = CarrierRegistrationForm()
    
    # Render registration template with form
    return render(request, template, {'form': form})


# Registration view - shows registration type selection page
# User chooses between company or carrier registration
def register_view(request):
    return render(request, 'accounts/register.html')


# Profile view - displays and allows editing of user profile
# Requires user to be logged in (@login_required decorator)
@login_required
def profile_view(request):
    from logistics.models import Route, Bid, Tracking
    from django.db.models import Count, Sum, Avg
    from django.forms import ModelForm
    
    context = {}
    edit_form = None
    
    # Handle company profile
    if request.user.role == 'company':
        # Try to get company profile (might not exist for new users)
        try:
            profile = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            profile = None
        
        # Handle profile editing form submission
        if request.method == 'POST' and 'edit_profile' in request.POST:
            # request.FILES needed for logo upload
            edit_form = CompanyProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Профіль успішно оновлено!')
                is_htmx = request.headers.get('HX-Request') == 'true'
                if is_htmx:
                    # Reload the page to show updated profile
                    return HttpResponse('<script>window.location.reload();</script>')
                return redirect('profile')
        else:
            # GET request - initialize form with existing profile data (if exists)
            if profile:
                edit_form = CompanyProfileEditForm(instance=profile, user=request.user)
            else:
                # No profile yet - show empty form
                edit_form = CompanyProfileEditForm(user=request.user)
        
        context['profile'] = profile
        context['edit_form'] = edit_form
        
        # Calculate statistics for company
        routes = Route.objects.filter(company=request.user)
        context['total_routes'] = routes.count()  # Total number of routes created
        context['pending_routes'] = routes.filter(status='pending').count()  # Routes waiting for carrier
        context['in_transit_routes'] = routes.filter(status='in_transit').count()  # Routes in progress
        context['delivered_routes'] = routes.filter(status='delivered').count()  # Completed routes
        # Total money spent on completed or in-progress routes
        context['total_spent'] = routes.filter(status__in=['in_transit', 'delivered']).aggregate(Sum('price'))['price__sum'] or 0
        context['recent_routes'] = routes.order_by('-created_at')[:5]  # 5 most recent routes
        context['all_routes'] = routes  # All routes for display
        
    # Handle carrier profile
    elif request.user.role == 'carrier':
        # Try to get carrier profile (might not exist for new users)
        try:
            profile = request.user.carrier_profile
        except CarrierProfile.DoesNotExist:
            profile = None
        
        # Handle profile editing form submission
        if request.method == 'POST' and 'edit_profile' in request.POST:
            edit_form = CarrierProfileEditForm(request.POST, instance=profile, user=request.user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Профіль успішно оновлено!')
                is_htmx = request.headers.get('HX-Request') == 'true'
                if is_htmx:
                    # Reload the page to show updated profile
                    return HttpResponse('<script>window.location.reload();</script>')
                return redirect('profile')
        else:
            # GET request - initialize form with existing profile data (if exists)
            if profile:
                edit_form = CarrierProfileEditForm(instance=profile, user=request.user)
            else:
                # No profile yet - show empty form
                edit_form = CarrierProfileEditForm(user=request.user)
        
        context['profile'] = profile
        context['edit_form'] = edit_form
        
        # Calculate statistics for carrier
        bids = Bid.objects.filter(carrier=request.user)
        routes = Route.objects.filter(carrier=request.user)
        context['total_bids'] = bids.count()  # Total number of bids made
        context['accepted_bids'] = bids.filter(is_accepted=True).count()  # Bids that were accepted
        context['completed_routes'] = routes.filter(status='delivered').count()  # Completed deliveries
        context['active_routes'] = routes.filter(status='in_transit').count()  # Currently active routes
        # Total money earned from completed routes
        context['total_earned'] = routes.filter(status='delivered').aggregate(Sum('price'))['price__sum'] or 0
        # Average price per completed route
        context['average_price'] = routes.filter(status='delivered').aggregate(Avg('price'))['price__avg'] or 0
        context['recent_bids'] = bids.order_by('-created_at')[:5]  # 5 most recent bids
        context['my_routes'] = routes.order_by('-created_at')[:5]  # 5 most recent routes
    
    # Check if user is admin (for admin panel access)
    context['is_admin'] = request.user.is_staff
    
    return render(request, 'accounts/profile.html', context)
