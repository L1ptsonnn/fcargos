from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import User, CompanyProfile, CarrierProfile
from .forms import LoginForm, CompanyRegistrationForm, CarrierRegistrationForm, CompanyProfileEditForm, CarrierProfileEditForm


# В'ю логіну: обробляє авторизацію користувача
# Запит GET показує форму
# Запит POST перевіряє дані та створює сесію
def login_view(request):
    # Якщо користувач уже в системі, перенаправляємо на головну
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('<script>window.location.href = "/";</script>')
        return redirect('home')
    
    # Визначаємо, чи це HTMX-запит
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'accounts/login_partial.html' if is_htmx else 'accounts/login.html'
    
    # Обробка POST-запиту з формою
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Забираємо логін і пароль із форми
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Перевіряємо облікові дані
            user = authenticate(request, username=username, password=password)
            if user:
                # Авторизуємо користувача (створюємо сесію)
                login(request, user)
                messages.success(request, f'Ласкаво просимо, {user.username}!')
                if is_htmx:
                    return HttpResponse('<script>window.location.href = "/";</script>')
                return redirect('home')
            else:
                # Невірні дані входу
                messages.error(request, 'Невірний логін або пароль')
    else:
        # На GET показуємо порожню форму
        form = LoginForm()
    
    # Рендеримо шаблон із формою
    return render(request, template, {'form': form})


# Реєстрація компанії: показує форму та створює профіль
# Запит GET повертає форму
# Запит POST створює користувача й CompanyProfile
def register_company(request):
    # Якщо користувач уже авторизований — на головну
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('<script>window.location.href = "/";</script>')
        return redirect('home')
    
    # Визначаємо HTMX-шаблон
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'accounts/register_company_partial.html' if is_htmx else 'accounts/register_company.html'
    
    # Якщо отримали POST — обробляємо дані
    if request.method == 'POST':
        # Поле request.FILES потрібне для логотипу
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = None
            try:
                # Виклик form.save() створює користувача з роллю company
                user = form.save()
                
                # Створюємо профіль компанії з полями з форми
                CompanyProfile.objects.create(
                    user=user,
                    address=form.cleaned_data.get('address', ''),
                    address_lat=form.cleaned_data.get('address_lat'),  # широта з мапи
                    address_lng=form.cleaned_data.get('address_lng'),  # довгота з мапи
                    tax_id=form.cleaned_data['tax_id'],  # податковий номер
                    description=form.cleaned_data.get('description', ''),  # необов'язковий опис
                    logo=form.cleaned_data.get('logo')  # необов'язковий логотип
                )
                messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
                if is_htmx:
                    return HttpResponse('<script>window.location.href = "/accounts/login/";</script>')
                return redirect('login')
            except Exception as e:
                # Якщо виникла помилка (наприклад, дублікат tax_id) — очищаємо користувача
                if user and user.pk:
                    user.delete()
                # Додаємо помилку до поля tax_id
                if 'tax_id' in str(e).lower() or 'unique' in str(e).lower():
                    form.add_error('tax_id', 'Компанія з таким податковим номером вже зареєстрована.')
                else:
                    messages.error(request, f'Помилка при реєстрації: {str(e)}')
    else:
        # На GET повертаємо порожню форму
        form = CompanyRegistrationForm()
    
    # Рендеримо шаблон із формою
    return render(request, template, {'form': form})


# Реєстрація перевізника: аналогічно створюємо користувача й профіль
# Запит GET віддає форму
# Запит POST зберігає користувача та CarrierProfile
def register_carrier(request):
    # Захист від повторної реєстрації авторизованих
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('<script>window.location.href = "/";</script>')
        return redirect('home')
    
    # Обираємо потрібний шаблон (HTMX чи ні)
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'accounts/register_carrier_partial.html' if is_htmx else 'accounts/register_carrier.html'
    
    # Запит POST зберігає дані
    if request.method == 'POST':
        form = CarrierRegistrationForm(request.POST)
        if form.is_valid():
            # Виклик form.save() одночасно створює User і CarrierProfile
            form.save()
            messages.success(request, 'Реєстрацію завершено! Будь ласка, увійдіть.')
            if is_htmx:
                return HttpResponse('<script>window.location.href = "/accounts/login/";</script>')
            return redirect('login')
    else:
        # На GET повертаємо порожню форму
        form = CarrierRegistrationForm()
    
    # Рендеримо шаблон із формою
    return render(request, template, {'form': form})


# Сторінка вибору типу реєстрації (компанія чи перевізник)
def register_view(request):
    return render(request, 'accounts/register.html')


# Профіль користувача: показуємо дані та дозволяємо редагування
# Потрібна авторизація (@login_required)
@login_required
def profile_view(request):
    from logistics.models import Route, Bid, Tracking
    from django.db.models import Count, Sum, Avg
    from django.forms import ModelForm
    
    context = {}
    edit_form = None
    
    # Гілка для компаній
    if request.user.role == 'company':
        # Можливо, профіль ще не створений
        try:
            profile = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            profile = None
        
        # Обробка редагування профілю
        if request.method == 'POST' and 'edit_profile' in request.POST:
            # Для логотипу потрібен request.FILES
            edit_form = CompanyProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Профіль успішно оновлено!')
                is_htmx = request.headers.get('HX-Request') == 'true'
                if is_htmx:
                    # Оновлюємо сторінку для відображення змін
                    return HttpResponse('<script>window.location.reload();</script>')
                return redirect('profile')
        else:
            # На GET підставляємо наявні дані
            if profile:
                edit_form = CompanyProfileEditForm(instance=profile, user=request.user)
            else:
                # Профіль відсутній — показуємо порожню форму
                edit_form = CompanyProfileEditForm(user=request.user)
        
        context['profile'] = profile
        context['edit_form'] = edit_form
        
        # Статистика для компанії
        routes = Route.objects.filter(company=request.user)
        context['total_routes'] = routes.count()  # усього створених маршрутів
        context['pending_routes'] = routes.filter(status='pending').count()  # очікують перевізника
        context['in_transit_routes'] = routes.filter(status='in_transit').count()  # в дорозі
        context['delivered_routes'] = routes.filter(status='delivered').count()  # доставлені
        # Витрати на активні та завершені маршрути
        context['total_spent'] = routes.filter(status__in=['in_transit', 'delivered']).aggregate(Sum('price'))['price__sum'] or 0
        context['recent_routes'] = routes.order_by('-created_at')[:5]  # останні 5 маршрутів
        context['all_routes'] = routes  # повний список для таблиці
        
    # Гілка для перевізників
    elif request.user.role == 'carrier':
        # Профіль може ще не існувати
        try:
            profile = request.user.carrier_profile
        except CarrierProfile.DoesNotExist:
            profile = None
        
        # Обробка редагування профілю
        if request.method == 'POST' and 'edit_profile' in request.POST:
            edit_form = CarrierProfileEditForm(request.POST, instance=profile, user=request.user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Профіль успішно оновлено!')
                is_htmx = request.headers.get('HX-Request') == 'true'
                if is_htmx:
                    # Перезавантажуємо, щоб показати зміни
                    return HttpResponse('<script>window.location.reload();</script>')
                return redirect('profile')
        else:
            # На GET підставляємо наявні значення
            if profile:
                edit_form = CarrierProfileEditForm(instance=profile, user=request.user)
            else:
                # Немає профілю — показуємо порожню форму
                edit_form = CarrierProfileEditForm(user=request.user)
        
        context['profile'] = profile
        context['edit_form'] = edit_form
        
        # Статистика для перевізника
        bids = Bid.objects.filter(carrier=request.user)
        routes = Route.objects.filter(carrier=request.user)
        context['total_bids'] = bids.count()  # усі ставки
        context['accepted_bids'] = bids.filter(is_accepted=True).count()  # прийняті ставки
        context['completed_routes'] = routes.filter(status='delivered').count()  # доставлені маршрути
        context['active_routes'] = routes.filter(status='in_transit').count()  # активні зараз
        # Дохід із завершених маршрутів
        context['total_earned'] = routes.filter(status='delivered').aggregate(Sum('price'))['price__sum'] or 0
        # Середній чек за доставку
        context['average_price'] = routes.filter(status='delivered').aggregate(Avg('price'))['price__avg'] or 0
        context['recent_bids'] = bids.order_by('-created_at')[:5]  # останні 5 ставок
        context['my_routes'] = routes.order_by('-created_at')[:5]  # останні 5 маршрутів
        
        # Рейтинг перевізника
        from logistics.models import Rating
        if profile:
            context['carrier_rating'] = profile.rating or 0.0
            context['rating_count'] = Rating.objects.filter(carrier=request.user).count()
        else:
            context['carrier_rating'] = 0.0
            context['rating_count'] = 0
    
    # Прапорець для відображення посилання в адмінку
    context['is_admin'] = request.user.is_staff
    
    return render(request, 'accounts/profile.html', context)
