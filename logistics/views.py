from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Route, Bid, Tracking, Message, Notification
from .forms import RouteForm, BidForm, TrackingUpdateForm, MessageForm


@login_required
def routes_list(request):
    """Список маршрутів"""
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user).order_by('-created_at')
    elif request.user.role == 'carrier':
        routes = Route.objects.filter(status='pending').order_by('-created_at')
    else:
        routes = Route.objects.none()
    
    # Фільтрація по місту старту
    origin_city_filter = request.GET.get('origin_city', '')
    if origin_city_filter:
        routes = routes.filter(origin_city__icontains=origin_city_filter)
    
    # Отримуємо список унікальних міст для фільтра
    origin_cities = Route.objects.values_list('origin_city', flat=True).distinct().order_by('origin_city')
    
    return render(request, 'logistics/routes_list.html', {
        'routes': routes,
        'origin_city_filter': origin_city_filter,
        'origin_cities': origin_cities,
    })


@login_required
def create_route(request):
    """Створення нового маршруту (тільки для компаній)"""
    if request.user.role != 'company':
        messages.error(request, 'Тільки компанії можуть створювати маршрути')
        return redirect('home')
    
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route.company = request.user
            route.save()
            # Створюємо Tracking з початковими значеннями
            Tracking.objects.create(
                route=route,
                current_location=route.origin_city,
                current_lat=route.origin_lat,
                current_lng=route.origin_lng,
                progress_percent=0
            )
            messages.success(request, 'Маршрут успішно створено!')
            return redirect('route_detail', pk=route.pk)
    else:
        form = RouteForm()
    
    return render(request, 'logistics/create_route.html', {'form': form})


@login_required
def route_detail(request, pk):
    """Деталі маршруту"""
    route = get_object_or_404(Route, pk=pk)
    bids = Bid.objects.filter(route=route).select_related('carrier').order_by('-created_at')
    can_bid = (request.user.role == 'carrier' and 
               route.status == 'pending' and
               not Bid.objects.filter(route=route, carrier=request.user).exists())
    
    # Перевірка можливості прийняти ставку (для компанії)
    can_accept_bids = (request.user.role == 'company' and 
                       route.company == request.user and 
                       route.status == 'pending')
    
    # Перевірка можливості завершити маршрут
    can_complete = ((request.user.role == 'carrier' and route.carrier == request.user) or
                   (request.user.role == 'company' and route.company == request.user)) and \
                   route.status == 'in_transit'
    
    # Обчислюємо різниці цін для ставок
    bids_with_diff = []
    for bid in bids:
        if route.price:
            if bid.proposed_price < route.price:
                diff = float(route.price) - float(bid.proposed_price)
                diff_type = 'discount'
            else:
                diff = float(bid.proposed_price) - float(route.price)
                diff_type = 'surcharge'
        else:
            diff = 0
            diff_type = None
        bids_with_diff.append({
            'bid': bid,
            'price_diff': diff,
            'diff_type': diff_type
        })
    
    # Перевірка та валідація координат
    try:
        origin_lat = float(route.origin_lat) if route.origin_lat else 50.45
        origin_lng = float(route.origin_lng) if route.origin_lng else 30.52
        dest_lat = float(route.destination_lat) if route.destination_lat else 49.84
        dest_lng = float(route.destination_lng) if route.destination_lng else 24.03
    except (ValueError, TypeError):
        origin_lat, origin_lng = 50.45, 30.52
        dest_lat, dest_lng = 49.84, 24.03
    
    # Рахуємо непрочитані повідомлення
    unread_messages_count = 0
    if route.carrier:
        unread_messages_count = Message.objects.filter(
            route=route, 
            recipient=request.user, 
            is_read=False
        ).count()
    
    context = {
        'route': route,
        'bids_with_diff': bids_with_diff,
        'can_bid': can_bid,
        'can_accept_bids': can_accept_bids,
        'can_complete': can_complete,
        'unread_messages_count': unread_messages_count,
        'route_data': {
            'origin': {
                'lat': origin_lat,
                'lng': origin_lng,
            },
            'destination': {
                'lat': dest_lat,
                'lng': dest_lng,
            },
        }
    }
    return render(request, 'logistics/route_detail.html', context)


@login_required
def create_bid(request, pk):
    """Створення ставки на маршрут"""
    if request.user.role != 'carrier':
        messages.error(request, 'Тільки перевізники можуть робити ставки')
        return redirect('home')
    
    route = get_object_or_404(Route, pk=pk)
    
    if route.status != 'pending':
        messages.error(request, 'На цей маршрут неможливо зробити ставку')
        return redirect('route_detail', pk=pk)
    
    if Bid.objects.filter(route=route, carrier=request.user).exists():
        messages.error(request, 'Ви вже зробили ставку на цей маршрут')
        return redirect('route_detail', pk=pk)
    
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.route = route
            bid.carrier = request.user
            bid.save()
            
            # Створюємо сповіщення для компанії
            Notification.objects.create(
                user=route.company,
                notification_type='new_bid',
                title='Нова ставка',
                message=f'Перевізник {request.user.username} зробив ставку на маршрут {route.origin_city} → {route.destination_city}',
                route=route
            )
            
            messages.success(request, 'Ставку успішно створено!')
            return redirect('route_detail', pk=pk)
    else:
        form = BidForm()
    
    return render(request, 'logistics/create_bid.html', {'form': form, 'route': route})


@login_required
def accept_bid(request, bid_id):
    """Прийняття ставки (тільки для компаній)"""
    if request.user.role != 'company':
        messages.error(request, 'Тільки компанії можуть приймати ставки')
        return redirect('home')
    
    bid = get_object_or_404(Bid, pk=bid_id, route__company=request.user)
    
    if bid.route.status != 'pending':
        messages.error(request, 'Цей маршрут вже не доступний')
        return redirect('route_detail', pk=bid.route.pk)
    
    # Відмічаємо ставку як прийняту
    bid.is_accepted = True
    bid.save()
    
    # Призначаємо перевізника маршруту
    bid.route.carrier = bid.carrier
    bid.route.status = 'in_transit'
    bid.route.price = bid.proposed_price
    bid.route.save()
    
    # Створюємо відстеження якщо його немає
    Tracking.objects.get_or_create(route=bid.route, defaults={
        'current_location': bid.route.origin_city,
        'current_lat': bid.route.origin_lat,
        'current_lng': bid.route.origin_lng,
    })
    
    # Створюємо сповіщення для перевізника
    Notification.objects.create(
        user=bid.carrier,
        notification_type='bid_accepted',
        title='Вашу ставку прийнято!',
        message=f'Компанія {request.user.username} прийняла вашу ставку на маршрут {bid.route.origin_city} → {bid.route.destination_city}',
        route=bid.route
    )
    
    # Створюємо сповіщення про призначення маршруту
    Notification.objects.create(
        user=bid.carrier,
        notification_type='route_assigned',
        title='Вам призначено маршрут',
        message=f'Вам призначено маршрут {bid.route.origin_city} → {bid.route.destination_city}',
        route=bid.route
    )
    
    messages.success(request, f'Ставку від {bid.carrier.username} прийнято!')
    return redirect('route_detail', pk=bid.route.pk)


@login_required
def complete_route(request, pk):
    """Завершення маршруту"""
    route = get_object_or_404(Route, pk=pk)
    
    if route.carrier != request.user and route.company != request.user:
        messages.error(request, 'У вас немає доступу до цього маршруту')
        return redirect('home')
    
    if route.status != 'in_transit':
        messages.error(request, 'Маршрут не може бути завершеним')
        return redirect('route_detail', pk=route.pk)
    
    route.status = 'delivered'
    route.save()
    
    # Створюємо сповіщення про завершення маршруту
    if route.carrier:
        Notification.objects.create(
            user=route.carrier,
            notification_type='route_completed',
            title='Маршрут завершено',
            message=f'Маршрут {route.origin_city} → {route.destination_city} успішно завершено',
            route=route
        )
    Notification.objects.create(
        user=route.company,
        notification_type='route_completed',
        title='Маршрут завершено',
        message=f'Маршрут {route.origin_city} → {route.destination_city} успішно завершено',
        route=route
    )
    
    # Оновлюємо відстеження до 100%
    try:
        tracking = route.tracking
        tracking.current_location = route.destination_city
        tracking.current_lat = route.destination_lat
        tracking.current_lng = route.destination_lng
        tracking.progress_percent = 100
        tracking.save()
    except Tracking.DoesNotExist:
        Tracking.objects.create(
            route=route,
            current_location=route.destination_city,
            current_lat=route.destination_lat,
            current_lng=route.destination_lng,
            progress_percent=100
        )
    
    messages.success(request, 'Маршрут успішно завершено!')
    return redirect('route_detail', pk=route.pk)


@login_required
def tracking_view(request, pk):
    """Відстеження маршруту"""
    route = get_object_or_404(Route, pk=pk)
    
    # Перевірка доступу
    if route.company != request.user and route.carrier != request.user:
        messages.error(request, 'У вас немає доступу до цього маршруту')
        return redirect('home')
    
    try:
        tracking = route.tracking
        # Якщо current_location порожнє, ініціалізуємо його
        if not tracking.current_location:
            tracking.current_location = route.origin_city
            if not tracking.current_lat:
                tracking.current_lat = route.origin_lat
            if not tracking.current_lng:
                tracking.current_lng = route.origin_lng
            tracking.save()
    except Tracking.DoesNotExist:
        # Створюємо Tracking з початковими значеннями
        tracking = Tracking.objects.create(
            route=route,
            current_location=route.origin_city,
            current_lat=route.origin_lat,
            current_lng=route.origin_lng,
            progress_percent=0
        )
    
    # Перевірка та валідація координат
    try:
        origin_lat = float(route.origin_lat) if route.origin_lat else 50.45
        origin_lng = float(route.origin_lng) if route.origin_lng else 30.52
        dest_lat = float(route.destination_lat) if route.destination_lat else 49.84
        dest_lng = float(route.destination_lng) if route.destination_lng else 24.03
        
        # Розраховуємо позицію на основі прогресу
        progress = max(0, min(100, tracking.progress_percent)) / 100.0
        current_lat = origin_lat + (dest_lat - origin_lat) * progress
        current_lng = origin_lng + (dest_lng - origin_lng) * progress
        
        # Розраховуємо прогрес на основі часу (якщо маршрут в дорозі)
        if route.status == 'in_transit' and route.pickup_date and route.delivery_date:
            from django.utils import timezone
            now = timezone.now()
            if route.pickup_date <= now <= route.delivery_date:
                total_time = (route.delivery_date - route.pickup_date).total_seconds()
                elapsed_time = (now - route.pickup_date).total_seconds()
                time_progress = min(100, max(0, int((elapsed_time / total_time) * 100)))
                # Оновлюємо прогрес якщо він відрізняється більше ніж на 5%
                if abs(time_progress - tracking.progress_percent) > 5:
                    tracking.progress_percent = time_progress
                    tracking.current_lat = current_lat
                    tracking.current_lng = current_lng
                    tracking.save()
    except (ValueError, TypeError):
        origin_lat, origin_lng = 50.45, 30.52
        dest_lat, dest_lng = 49.84, 24.03
        current_lat, current_lng = origin_lat, origin_lng
    
    # Форма для оновлення прогресу (тільки для перевізника)
    can_update = (request.user.role == 'carrier' and route.carrier == request.user and route.status == 'in_transit')
    
    form = None
    if can_update and request.method == 'GET':
        form = TrackingUpdateForm(instance=tracking)
    elif can_update and request.method == 'POST':
        form = TrackingUpdateForm(request.POST, instance=tracking)
        if form.is_valid():
            tracking = form.save(commit=False)
            
            # Завжди автоматично розраховуємо координати на основі прогресу
            try:
                origin_lat = float(route.origin_lat)
                origin_lng = float(route.origin_lng)
                dest_lat = float(route.destination_lat)
                dest_lng = float(route.destination_lng)
                
                progress = max(0, min(100, tracking.progress_percent)) / 100.0
                tracking.current_lat = origin_lat + (dest_lat - origin_lat) * progress
                tracking.current_lng = origin_lng + (dest_lng - origin_lng) * progress
            except (ValueError, TypeError):
                pass
            
            # Якщо прогрес 100%, автоматично оновлюємо локацію на призначення
            if tracking.progress_percent >= 100:
                tracking.current_location = route.destination_city
                tracking.current_lat = route.destination_lat
                tracking.current_lng = route.destination_lng
            
            tracking.save()
            messages.success(request, f'Прогрес оновлено до {tracking.progress_percent}%')
            # Оновлюємо координати для контексту
            try:
                current_lat = float(tracking.current_lat) if tracking.current_lat else origin_lat
                current_lng = float(tracking.current_lng) if tracking.current_lng else origin_lng
            except (ValueError, TypeError, NameError):
                current_lat, current_lng = origin_lat, origin_lng
    
    context = {
        'route': route,
        'tracking': tracking,
        'form': form,
        'can_update': can_update,
        'route_data': {
            'origin': {
                'lat': origin_lat,
                'lng': origin_lng,
            },
            'destination': {
                'lat': dest_lat,
                'lng': dest_lng,
            },
            'current': {
                'lat': current_lat,
                'lng': current_lng,
            }
        }
    }
    return render(request, 'logistics/tracking.html', context)


@login_required
def update_tracking(request, pk):
    """Оновлення прогресу доставки"""
    route = get_object_or_404(Route, pk=pk)
    
    try:
        tracking = route.tracking
    except Tracking.DoesNotExist:
        tracking = Tracking.objects.create(
            route=route,
            current_location=route.origin_city,
            current_lat=route.origin_lat,
            current_lng=route.origin_lng,
            progress_percent=0
        )
    
    # Перевірка доступу - тільки перевізник може оновлювати
    if not (request.user.role == 'carrier' and route.carrier == request.user):
        messages.error(request, 'Тільки перевізник може оновлювати прогрес доставки')
        return redirect('tracking', pk=route.pk)
    
    # Перевірка статусу - можна оновлювати тільки якщо в дорозі
    if route.status != 'in_transit':
        messages.error(request, 'Можна оновлювати прогрес тільки для маршрутів у статусі "В дорозі"')
        return redirect('tracking', pk=route.pk)
    
    if request.method == 'POST':
        form = TrackingUpdateForm(request.POST, instance=tracking)
        if form.is_valid():
            tracking = form.save(commit=False)
            
            # Обмежуємо прогрес до 100%
            if tracking.progress_percent > 100:
                tracking.progress_percent = 100
            if tracking.progress_percent < 0:
                tracking.progress_percent = 0
            
            # Завжди автоматично розраховуємо координати на основі прогресу
            try:
                origin_lat = float(route.origin_lat)
                origin_lng = float(route.origin_lng)
                dest_lat = float(route.destination_lat)
                dest_lng = float(route.destination_lng)
                
                progress = max(0, min(100, tracking.progress_percent)) / 100.0
                tracking.current_lat = origin_lat + (dest_lat - origin_lat) * progress
                tracking.current_lng = origin_lng + (dest_lng - origin_lng) * progress
            except (ValueError, TypeError):
                pass
            
            # Якщо прогрес 100%, автоматично оновлюємо локацію на призначення
            if tracking.progress_percent >= 100:
                tracking.current_location = route.destination_city
                tracking.current_lat = route.destination_lat
                tracking.current_lng = route.destination_lng
                tracking.progress_percent = 100  # Забезпечуємо максимум
                messages.info(request, 'Прогрес доставки 100%! Рекомендується завершити маршрут на сторінці деталей.')
            
            tracking.save()
            
            # Створюємо сповіщення для компанії про оновлення відстеження
            if route.company:
                Notification.objects.create(
                    user=route.company,
                    notification_type='tracking_updated',
                    title='Оновлено відстеження',
                    message=f'Прогрес доставки оновлено до {tracking.progress_percent}% для маршруту {route.origin_city} → {route.destination_city}',
                    route=route
                )
            
            messages.success(request, f'Прогрес оновлено до {tracking.progress_percent}%')
            return redirect('tracking', pk=route.pk)
    else:
        form = TrackingUpdateForm(instance=tracking)
    
    return redirect('tracking', pk=route.pk)


@login_required
def route_messages(request, pk):
    """Месенджер для маршруту"""
    route = get_object_or_404(Route, pk=pk)
    
    # Перевірка доступу
    if route.company != request.user and (not route.carrier or route.carrier != request.user):
        messages.error(request, 'У вас немає доступу до цього маршруту')
        return redirect('home')
    
    # Визначаємо співрозмовника
    if request.user == route.company:
        other_user = route.carrier
    elif request.user == route.carrier:
        other_user = route.company
    else:
        other_user = None
    
    # Якщо перевізник ще не призначений, не показуємо месенджер
    if not route.carrier:
        messages.info(request, 'Месенджер стане доступним після призначення перевізника')
        return redirect('route_detail', pk=route.pk)
    
    if not other_user:
        messages.error(request, 'Неможливо визначити співрозмовника')
        return redirect('route_detail', pk=route.pk)
    
    # Отримуємо повідомлення для цього маршруту
    messages_list = Message.objects.filter(route=route).order_by('created_at')
    
    # Позначаємо повідомлення як прочитані
    Message.objects.filter(route=route, recipient=request.user, is_read=False).update(is_read=True)
    
    # Обробка форми відправки повідомлення
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.route = route
            message.sender = request.user
            message.recipient = other_user
            message.save()
            
            # Створюємо сповіщення для отримувача
            Notification.objects.create(
                user=other_user,
                notification_type='new_message',
                title='Нове повідомлення',
                message=f'Від {request.user.username}: {message.content[:50]}...',
                route=route
            )
            
            messages.success(request, 'Повідомлення відправлено!')
            return redirect('route_messages', pk=route.pk)
    else:
        form = MessageForm()
    
    # Рахуємо непрочитані повідомлення
    unread_count = Message.objects.filter(route=route, recipient=request.user, is_read=False).count()
    
    context = {
        'route': route,
        'other_user': other_user,
        'messages_list': messages_list,
        'form': form,
        'unread_count': unread_count,
    }
    return render(request, 'logistics/messages.html', context)


@login_required
def chats_list(request):
    """Список всіх чатів користувача"""
    # Отримуємо всі маршрути де користувач є учасником
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user, carrier__isnull=False).order_by('-created_at')
    elif request.user.role == 'carrier':
        routes = Route.objects.filter(carrier=request.user).order_by('-created_at')
    else:
        routes = Route.objects.none()
    
    # Для кожного маршруту отримуємо останнє повідомлення та кількість непрочитаних
    chats_data = []
    for route in routes:
        other_user = route.carrier if request.user == route.company else route.company
        
        last_message = Message.objects.filter(route=route).order_by('-created_at').first()
        unread_count = Message.objects.filter(route=route, recipient=request.user, is_read=False).count()
        
        chats_data.append({
            'route': route,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    return render(request, 'logistics/chats_list.html', {'chats_data': chats_data})


@login_required
def chats_unread_count(request):
    """API для отримання кількості непрочитаних повідомлень в чатах"""
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user, carrier__isnull=False)
    elif request.user.role == 'carrier':
        routes = Route.objects.filter(carrier=request.user)
    else:
        routes = Route.objects.none()
    
    total_unread = 0
    for route in routes:
        unread_count = Message.objects.filter(route=route, recipient=request.user, is_read=False).count()
        total_unread += unread_count
    
    return JsonResponse({'unread_count': total_unread})


@login_required
def user_profile(request, user_id):
    """Профіль користувача"""
    from accounts.models import User
    profile_user = get_object_or_404(User, pk=user_id)
    
    # Статистика маршрутів
    if profile_user.role == 'company':
        routes_created = Route.objects.filter(company=profile_user).count()
        routes_in_transit = Route.objects.filter(company=profile_user, status='in_transit').count()
        routes_completed = Route.objects.filter(company=profile_user, status='delivered').count()
    else:
        routes_created = 0
        routes_in_transit = Route.objects.filter(carrier=profile_user, status='in_transit').count()
        routes_completed = Route.objects.filter(carrier=profile_user, status='delivered').count()
    
    context = {
        'profile_user': profile_user,
        'routes_created': routes_created,
        'routes_in_transit': routes_in_transit,
        'routes_completed': routes_completed,
    }
    return render(request, 'logistics/user_profile.html', context)


@login_required
def notifications_api(request):
    """API для отримання сповіщень (AJAX)"""
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    
    notifications_data = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
        'route_id': n.route.id if n.route else None,
    } for n in notifications]
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count,
    })


@login_required
def mark_notification_read(request, notification_id):
    """Позначити сповіщення як прочитане"""
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('home')


@login_required
def mark_all_notifications_read(request):
    """Позначити всі сповіщення як прочитані"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'Всі сповіщення позначено як прочитані')
    return redirect('home')
