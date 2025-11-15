from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from .models import Route, Bid, Tracking, Message, Notification, Rating
from .forms import RouteForm, BidForm, TrackingUpdateForm, MessageForm, RatingForm


# Function to check and mark expired routes
# Routes expire if no bid was accepted before pickup_date
def check_expired_routes():
    """Check and mark expired routes"""
    now = timezone.now()
    
    # Find routes that meet all these conditions:
    # 1. Status is 'pending' (not yet accepted)
    # 2. No carrier assigned (carrier = None)
    # 3. Pickup date has passed (pickup_date < now)
    expired_routes = Route.objects.filter(
        status='pending',
        carrier__isnull=True,
        pickup_date__lt=now
    )
    
    expired_count = 0
    for route in expired_routes:
        # Update route status to 'expired'
        route.status = 'expired'
        route.save()
        
        # Check if notification about expiration already exists (to avoid duplicates)
        existing_notification = Notification.objects.filter(
            user=route.company,
            notification_type='route_expired',
            route=route
        ).exists()
        
        # Create notification only if it doesn't exist yet
        if not existing_notification:
            # Convert date to local timezone (Europe/Kyiv)
            pickup_date_local = timezone.localtime(route.pickup_date) if timezone.is_aware(route.pickup_date) else route.pickup_date
            Notification.objects.create(
                user=route.company,
                notification_type='route_expired',
                title='Маршрут просрочений',
                message=f'Маршрут {route.origin_city} → {route.destination_city} просрочений. Ніхто не прийняв ставку до часу забору ({pickup_date_local.strftime("%d.%m.%Y %H:%M")}).',
                route=route
            )
            expired_count += 1
    
    return expired_count


# Routes list view - displays routes based on user role
# Companies see their own routes, carriers see available routes
@login_required
def routes_list(request):
    """Routes list view"""
    # Check for expired routes before displaying list
    check_expired_routes()
    
    # Get routes based on user role
    if request.user.role == 'company':
        # Companies see all their own routes (all statuses)
        routes = Route.objects.filter(company=request.user).order_by('-created_at')
    elif request.user.role == 'carrier':
        # Carriers see only pending routes (not expired, not assigned)
        routes = Route.objects.filter(status='pending').order_by('-created_at')
    else:
        # Anonymous or other roles - no routes
        routes = Route.objects.none()
    
    # Filter by origin city (can be from search or filter dropdown)
    origin_city_filter = request.GET.get('origin_city', '')
    search_city = request.GET.get('search_city', '')
    city_filter = origin_city_filter or search_city
    if city_filter:
        # Case-insensitive search for city name
        routes = routes.filter(origin_city__icontains=city_filter)
    
    # Filter by status (can select multiple statuses)
    status_filter = request.GET.getlist('status')
    if status_filter:
        routes = routes.filter(status__in=status_filter)
    
    # Get list of unique cities for filter dropdown
    origin_cities = Route.objects.values_list('origin_city', flat=True).distinct().order_by('origin_city')
    
    # AJAX request to get cities list (for autocomplete)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'get_cities' in request.GET:
        return JsonResponse({'cities': list(origin_cities)})
    
    # AJAX request to get routes in JSON format (for dynamic loading)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'format' in request.GET and request.GET.get('format') == 'json':
        routes_data = []
        for route in routes:
            # Convert dates to local timezone (UTC+2 for Ukraine/Europe/Kyiv)
            pickup_date_local = None
            delivery_date_local = None
            if route.pickup_date:
                # Check if date is timezone-aware (has timezone info)
                if timezone.is_aware(route.pickup_date):
                    # Convert from UTC to local time (Europe/Kyiv)
                    pickup_date_local = timezone.localtime(route.pickup_date)
                else:
                    # Date is naive (no timezone) - use as is
                    pickup_date_local = route.pickup_date
            if route.delivery_date:
                if timezone.is_aware(route.delivery_date):
                    delivery_date_local = timezone.localtime(route.delivery_date)
                else:
                    delivery_date_local = route.delivery_date
            
            # Build route data dictionary for JSON response
            route_data = {
                'id': route.id,
                'origin_city': route.origin_city,
                'destination_city': route.destination_city,
                'cargo_type': route.cargo_type,
                'weight': str(route.weight),  # Convert to string for JSON
                'price': str(route.price),    # Convert to string for JSON
                'status': route.status,
                'pickup_date': pickup_date_local.strftime('%d.%m.%Y %H:%M') if pickup_date_local else None,
                'delivery_date': delivery_date_local.strftime('%d.%m.%Y %H:%M') if delivery_date_local else None,
                'company_id': route.company.pk if route.company else None,
                'company_name': route.company.company_name if route.company and route.company.company_name else route.company.username if route.company else None,
            }
            
            # Add carrier information if route has assigned carrier
            if route.carrier:
                route_data['carrier_id'] = route.carrier.pk
                route_data['carrier_name'] = route.carrier.username
                # Add carrier rating if available
                try:
                    if route.carrier.carrier_profile and route.carrier.carrier_profile.rating > 0:
                        route_data['carrier_rating'] = float(route.carrier.carrier_profile.rating)
                except:
                    pass  # If error, just skip rating
            
            routes_data.append(route_data)
        return JsonResponse({'routes': routes_data})
    
    return render(request, 'logistics/routes_list.html', {
        'routes': routes,
        'origin_city_filter': origin_city_filter,
        'origin_cities': origin_cities,
    })


# Create route view - allows companies to create new delivery routes
# Only company users can access this view
@login_required
def create_route(request):
    """Create new route (only for companies)"""
    # Check if user is a company
    if request.user.role != 'company':
        messages.error(request, 'Тільки компанії можуть створювати маршрути')
        return redirect('home')
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'logistics/create_route_partial.html' if is_htmx else 'logistics/create_route.html'
    
    # If form was submitted (POST request)
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            # Save route but don't commit yet (commit=False)
            # This allows us to set company field before saving
            route = form.save(commit=False)
            route.company = request.user  # Set route owner to current user
            route.save()
            
            # Create Tracking object with initial values (cargo starts at origin)
            Tracking.objects.create(
                route=route,
                current_location=route.origin_city,
                current_lat=route.origin_lat,
                current_lng=route.origin_lng,
                progress_percent=0  # Progress starts at 0%
            )
            messages.success(request, 'Маршрут успішно створено!')
            if is_htmx:
                return HttpResponse(f'<script>window.location.href = "/logistics/routes/{route.pk}/";</script>')
            return redirect('route_detail', pk=route.pk)
    else:
        # GET request - show empty form
        form = RouteForm()
    
    return render(request, template, {'form': form})


# Route detail view - shows detailed information about a route
# Displays route info, bids, map, and allows actions (bid, accept, complete)
@login_required
def route_detail(request, pk):
    """Route details view"""
    # Get route by ID, return 404 if not found
    route = get_object_or_404(Route, pk=pk)
    
    # Get all bids for this route, ordered by creation date (newest first)
    # select_related('carrier') optimizes database query (joins carrier data)
    bids = Bid.objects.filter(route=route).select_related('carrier').order_by('-created_at')
    
    # Check if current user (carrier) can make a bid on this route
    # Conditions: user is carrier, route is pending, user hasn't bid yet
    can_bid = (request.user.role == 'carrier' and 
               route.status == 'pending' and
               not Bid.objects.filter(route=route, carrier=request.user).exists())
    
    # Check if company can accept bids (company owns route and route is pending)
    can_accept_bids = (request.user.role == 'company' and 
                       route.company == request.user and 
                       route.status == 'pending')
    
    # Check if user can complete the route (carrier or company, route is in_transit)
    can_complete = ((request.user.role == 'carrier' and route.carrier == request.user) or
                   (request.user.role == 'company' and route.company == request.user)) and \
                   route.status == 'in_transit'
    
    # Calculate price differences for bids (how much cheaper/expensive compared to route price)
    bids_with_diff = []
    for bid in bids:
        if route.price:
            if bid.proposed_price < route.price:
                # Carrier offers discount
                diff = float(route.price) - float(bid.proposed_price)
                diff_type = 'discount'
            else:
                # Carrier asks for surcharge
                diff = float(bid.proposed_price) - float(route.price)
                diff_type = 'surcharge'
        else:
            diff = 0
            diff_type = None
        bids_with_diff.append({
            'bid': bid,
            'price_diff': diff,
            'diff_type': diff_type  # 'discount' or 'surcharge'
        })
    
    # Validate and convert coordinates for map display
    # Default coordinates are Kyiv (50.45, 30.52) and Lviv (49.84, 24.03)
    try:
        origin_lat = float(route.origin_lat) if route.origin_lat else 50.45
        origin_lng = float(route.origin_lng) if route.origin_lng else 30.52
        dest_lat = float(route.destination_lat) if route.destination_lat else 49.84
        dest_lng = float(route.destination_lng) if route.destination_lng else 24.03
    except (ValueError, TypeError):
        # If conversion fails, use default coordinates
        origin_lat, origin_lng = 50.45, 30.52  # Kyiv
        dest_lat, dest_lng = 49.84, 24.03      # Lviv
    
    # Count unread messages for current user related to this route
    unread_messages_count = 0
    if route.carrier:
        unread_messages_count = Message.objects.filter(
            route=route, 
            recipient=request.user,  # Messages received by current user
            is_read=False  # Only unread messages
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


# Create bid view - allows carriers to make bids on routes
# Only carrier users can access this view
# Supports both regular POST and AJAX requests
@login_required
def create_bid(request, pk):
    """Create bid on route"""
    # Check if user is a carrier
    if request.user.role != 'carrier':
        # Handle AJAX request differently (return JSON)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Тільки перевізники можуть робити ставки'}, status=403)
        messages.error(request, 'Тільки перевізники можуть робити ставки')
        return redirect('home')
    
    route = get_object_or_404(Route, pk=pk)
    
    # Check if route is still available for bidding
    if route.status != 'pending':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'На цей маршрут неможливо зробити ставку'}, status=400)
        messages.error(request, 'На цей маршрут неможливо зробити ставку')
        return redirect('route_detail', pk=pk)
    
    # Check if carrier already made a bid on this route
    if Bid.objects.filter(route=route, carrier=request.user).exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Ви вже зробили ставку на цей маршрут'}, status=400)
        messages.error(request, 'Ви вже зробили ставку на цей маршрут')
        return redirect('route_detail', pk=pk)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # If form was submitted (POST request)
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            # Save bid but don't commit yet
            bid = form.save(commit=False)
            bid.route = route
            bid.carrier = request.user  # Set bid owner to current user
            bid.save()
            
            # Create notification for company about new bid
            Notification.objects.create(
                user=route.company,
                notification_type='new_bid',
                title='Нова ставка',
                message=f'Перевізник {request.user.username} зробив ставку на маршрут {route.origin_city} → {route.destination_city}',
                route=route
            )
            
            # Return appropriate response based on request type
            if is_htmx:
                return HttpResponse('<div class="alert alert-success">Ставку успішно створено!</div><script>setTimeout(() => window.location.reload(), 1500);</script>')
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Ставку успішно створено!'})
            messages.success(request, 'Ставку успішно створено!')
            return redirect('route_detail', pk=pk)
    else:
        # GET request - show empty form
        form = BidForm()
    
    # For HTMX/AJAX requests, return only the form HTML (for modal)
    if is_htmx or is_ajax:
        template = 'logistics/create_bid_partial.html' if is_htmx else 'logistics/create_bid.html'
        html = render_to_string(template, {
            'route': route,
            'form': form
        }, request=request)
        if is_htmx:
            return HttpResponse(html)
        return JsonResponse({'html': html})
    
    # Regular request - render full page
    return render(request, 'logistics/create_bid.html', {'form': form, 'route': route})


# Accept bid view - allows companies to accept a carrier's bid
# Only company users can access this view
@login_required
def accept_bid(request, bid_id):
    """Accept bid (only for companies)"""
    # Check if user is a company
    if request.user.role != 'company':
        messages.error(request, 'Тільки компанії можуть приймати ставки')
        return redirect('home')
    
    # Get bid, ensuring it belongs to a route owned by current company
    bid = get_object_or_404(Bid, pk=bid_id, route__company=request.user)
    
    # Check if route is still available for accepting bids
    if bid.route.status != 'pending':
        messages.error(request, 'Цей маршрут вже не доступний')
        return redirect('route_detail', pk=bid.route.pk)
    
    # Mark bid as accepted
    bid.is_accepted = True
    bid.save()
    
    # Assign carrier to route and update route status
    bid.route.carrier = bid.carrier  # Set carrier to bid owner
    bid.route.status = 'in_transit'  # Change status to "in transit"
    bid.route.price = bid.proposed_price  # Update price to bid price
    bid.route.save()
    
    # Create tracking object if it doesn't exist (for route monitoring)
    Tracking.objects.get_or_create(route=bid.route, defaults={
        'current_location': bid.route.origin_city,
        'current_lat': bid.route.origin_lat,
        'current_lng': bid.route.origin_lng,
        'progress_percent': 0
    })
    
    # Create notification for carrier about accepted bid
    Notification.objects.create(
        user=bid.carrier,
        notification_type='bid_accepted',
        title='Вашу ставку прийнято!',
        message=f'Компанія {request.user.username} прийняла вашу ставку на маршрут {bid.route.origin_city} → {bid.route.destination_city}',
        route=bid.route
    )
    
    # Create notification for carrier about route assignment
    Notification.objects.create(
        user=bid.carrier,
        notification_type='route_assigned',
        title='Вам призначено маршрут',
        message=f'Вам призначено маршрут {bid.route.origin_city} → {bid.route.destination_city}',
        route=bid.route
    )
    
    messages.success(request, f'Ставку від {bid.carrier.username} прийнято!')
    is_htmx = request.headers.get('HX-Request') == 'true'
    if is_htmx:
        return HttpResponse(f'<script>window.location.href = "/logistics/routes/{bid.route.pk}/";</script>')
    return redirect('route_detail', pk=bid.route.pk)


# Complete route view - marks route as delivered/completed
# Can be called by either carrier or company
@login_required
def complete_route(request, pk):
    """Complete route"""
    route = get_object_or_404(Route, pk=pk)
    
    # Check access - only route carrier or company owner can complete
    if route.carrier != request.user and route.company != request.user:
        messages.error(request, 'У вас немає доступу до цього маршруту')
        return redirect('home')
    
    # Check if route is in correct status for completion
    if route.status != 'in_transit':
        messages.error(request, 'Маршрут не може бути завершеним')
        return redirect('route_detail', pk=route.pk)
    
    # Update route status to delivered
    route.status = 'delivered'
    route.save()
    
    # Create notifications about route completion
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
    
    # Update tracking to 100% completion (cargo reached destination)
    try:
        tracking = route.tracking
        tracking.current_location = route.destination_city
        tracking.current_lat = route.destination_lat
        tracking.current_lng = route.destination_lng
        tracking.progress_percent = 100
        tracking.save()
    except Tracking.DoesNotExist:
        # If tracking doesn't exist, create it with 100% progress
        Tracking.objects.create(
            route=route,
            current_location=route.destination_city,
            current_lat=route.destination_lat,
            current_lng=route.destination_lng,
            progress_percent=100
        )
    
    messages.success(request, 'Маршрут успішно завершено!')
    is_htmx = request.headers.get('HX-Request') == 'true'
    if is_htmx:
        return HttpResponse(f'<script>window.location.href = "/logistics/routes/{route.pk}/";</script>')
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
def route_messages_api(request, pk):
    """API для отримання повідомлень маршруту (AJAX/HTMX)"""
    route = get_object_or_404(Route, pk=pk)
    
    # Перевірка доступу
    if route.company != request.user and (not route.carrier or route.carrier != request.user):
        if request.headers.get('HX-Request'):
            return HttpResponse('<div class="alert alert-danger">Access denied</div>', status=403)
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Визначаємо співрозмовника
    if request.user == route.company:
        other_user = route.carrier
    elif request.user == route.carrier:
        other_user = route.company
    else:
        if request.headers.get('HX-Request'):
            return HttpResponse('<div class="alert alert-danger">Invalid user</div>', status=403)
        return JsonResponse({'error': 'Invalid user'}, status=403)
    
    if not route.carrier or not other_user:
        if request.headers.get('HX-Request'):
            return HttpResponse('<div class="alert alert-danger">Invalid route</div>', status=404)
        return JsonResponse({'error': 'Invalid route'}, status=404)
    
    # Отримуємо повідомлення
    messages_list = Message.objects.filter(route=route).order_by('created_at')
    
    # Позначаємо як прочитані
    Message.objects.filter(route=route, recipient=request.user, is_read=False).update(is_read=True)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if is_htmx:
        # Return HTML for HTMX
        html = render_to_string('logistics/messages_partial.html', {
            'messages': messages_list,
            'other_user': other_user,
            'route': route,
            'current_user_id': request.user.id,
        }, request=request)
        return HttpResponse(html)
    
    # Return JSON for AJAX
    messages_data = [{
        'id': msg.id,
        'sender': msg.sender.username,
        'sender_id': msg.sender.id,
        'content': msg.content,
        'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
        'is_read': msg.is_read,
    } for msg in messages_list]
    
    return JsonResponse({
        'messages': messages_data,
        'other_user': other_user.username,
        'route_origin': route.origin_city,
        'route_destination': route.destination_city,
    })


@login_required
def route_messages_send(request, pk):
    """API для відправки повідомлення (AJAX)"""
    route = get_object_or_404(Route, pk=pk)
    
    # Перевірка доступу
    if route.company != request.user and (not route.carrier or route.carrier != request.user):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Визначаємо співрозмовника
    if request.user == route.company:
        other_user = route.carrier
    elif request.user == route.carrier:
        other_user = route.company
    else:
        return JsonResponse({'error': 'Invalid user'}, status=403)
    
    if not route.carrier or not other_user:
        return JsonResponse({'error': 'Invalid route'}, status=404)
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if content:
            message = Message.objects.create(
                route=route,
                sender=request.user,
                recipient=other_user,
                content=content
            )
            
            # Створюємо сповіщення
            Notification.objects.create(
                user=other_user,
                notification_type='new_message',
                title='Нове повідомлення',
                message=f'Від {request.user.username}: {content[:50]}...',
                route=route
            )
            
            return JsonResponse({'success': True, 'message_id': message.id})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


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
def chats_api(request):
    """API для отримання чатів (AJAX/HTMX)"""
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user, carrier__isnull=False).order_by('-created_at')
    elif request.user.role == 'carrier':
        routes = Route.objects.filter(carrier=request.user).order_by('-created_at')
    else:
        routes = Route.objects.none()
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    chats_data = []
    total_unread = 0
    for route in routes:
        other_user = route.carrier if request.user == route.company else route.company
        last_message = Message.objects.filter(route=route).order_by('-created_at').first()
        unread_count = Message.objects.filter(route=route, recipient=request.user, is_read=False).count()
        total_unread += unread_count
        
        chats_data.append({
            'route_id': route.id,
            'other_user': other_user.username,
            'other_user_id': other_user.id,
            'other_user_role': other_user.get_role_display(),
            'route_origin': route.origin_city,
            'route_destination': route.destination_city,
            'route_status': route.get_status_display(),
            'last_message': last_message.content[:50] if last_message else None,
            'last_message_time': last_message.created_at.strftime('%d.%m.%Y %H:%M') if last_message else None,
            'unread_count': unread_count,
        })
    
    if is_htmx:
        # Return HTML for HTMX
        html = render_to_string('logistics/chats_partial.html', {
            'chats': chats_data,
            'total_unread': total_unread,
        }, request=request)
        return HttpResponse(html)
    
    # Return JSON for AJAX
    return JsonResponse({
        'chats': chats_data,
        'total_unread': total_unread,
    })


@login_required
def history_api(request):
    """API для отримання історії маршрутів (AJAX)"""
    from django.template.loader import render_to_string
    
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user).order_by('-created_at')
    elif request.user.role == 'carrier':
        routes = Route.objects.filter(carrier=request.user).order_by('-created_at')
    else:
        routes = Route.objects.none()
    
    html = render_to_string('dashboard/history_partial.html', {
        'routes': routes,
        'user': request.user
    }, request=request)
    
    return JsonResponse({'html': html})


def user_profile(request, user_id):
    """Профіль користувача (доступний для перегляду всім)"""
    from accounts.models import User, CarrierProfile, CompanyProfile
    from django.db.models import Sum, Avg, Count
    
    profile_user = get_object_or_404(User, pk=user_id)
    
    # Отримуємо профіль
    company_profile = None
    carrier_profile = None
    
    if profile_user.role == 'company':
        try:
            company_profile = profile_user.company_profile
        except CompanyProfile.DoesNotExist:
            pass
    else:
        try:
            carrier_profile = profile_user.carrier_profile
        except CarrierProfile.DoesNotExist:
            pass
    
    # Статистика маршрутів
    if profile_user.role == 'company':
        routes = Route.objects.filter(company=profile_user)
        routes_created = routes.count()
        routes_in_transit = routes.filter(status='in_transit').count()
        routes_completed = routes.filter(status='delivered').count()
        routes_pending = routes.filter(status='pending').count()
        total_spent = routes.filter(status__in=['in_transit', 'delivered']).aggregate(Sum('price'))['price__sum'] or 0
        recent_routes = routes.order_by('-created_at')[:5]
        ratings = None
        user_rating = None
    else:
        routes = Route.objects.filter(carrier=profile_user)
        bids = Bid.objects.filter(carrier=profile_user)
        routes_created = 0
        routes_in_transit = routes.filter(status='in_transit').count()
        routes_completed = routes.filter(status='delivered').count()
        routes_pending = 0
        total_spent = 0
        recent_routes = routes.order_by('-created_at')[:5]
        
        total_bids = bids.count()
        accepted_bids = bids.filter(is_accepted=True).count()
        total_earned = routes.filter(status='delivered').aggregate(Sum('price'))['price__sum'] or 0
        average_price = routes.filter(status='delivered').aggregate(Avg('price'))['price__avg'] or 0
        
        ratings = Rating.objects.filter(carrier=profile_user).select_related('company', 'route').order_by('-created_at')[:10]
        
        # Перевіряємо чи поточна компанія вже ставила оцінку цьому перевізнику
        if request.user.is_authenticated and request.user.role == 'company':
            user_rating = Rating.objects.filter(
                carrier=profile_user,
                company=request.user
            ).first()
        else:
            user_rating = None
    
    # Визначаємо чи це власний профіль
    is_own_profile = request.user.is_authenticated and request.user.pk == profile_user.pk
    
    # Обробка форми оцінки (тільки для авторизованих компаній)
    rating_form = None
    if request.user.is_authenticated and request.user.role == 'company' and profile_user.role == 'carrier' and not is_own_profile:
        if request.method == 'POST' and 'rating_submit' in request.POST:
            rating_form = RatingForm(request.POST)
            if rating_form.is_valid():
                route_id = request.POST.get('route_id')
                route = None
                if route_id:
                    try:
                        route = Route.objects.get(pk=route_id, company=request.user, carrier=profile_user)
                    except Route.DoesNotExist:
                        pass
                
                rating_obj, created = Rating.objects.update_or_create(
                    carrier=profile_user,
                    company=request.user,
                    route=route,
                    defaults={
                        'rating': int(rating_form.cleaned_data['rating']),
                        'comment': rating_form.cleaned_data['comment']
                    }
                )
                
                messages.success(request, 'Оцінку успішно збережено!')
                return redirect('user_profile', user_id=user_id)
        else:
            if user_rating:
                rating_form = RatingForm(instance=user_rating)
            else:
                rating_form = RatingForm()
    
    context = {
        'profile_user': profile_user,
        'company_profile': company_profile,
        'carrier_profile': carrier_profile,
        'routes_created': routes_created,
        'routes_in_transit': routes_in_transit,
        'routes_completed': routes_completed,
        'routes_pending': routes_pending if profile_user.role == 'company' else 0,
        'total_spent': total_spent if profile_user.role == 'company' else 0,
        'recent_routes': recent_routes,
        'ratings': ratings,
        'user_rating': user_rating,
        'rating_form': rating_form,
        'is_own_profile': is_own_profile,
        'user': request.user,  # Для перевірки в template
    }
    
    # Додаткова статистика для перевізника
    if profile_user.role == 'carrier':
        context.update({
            'total_bids': total_bids,
            'accepted_bids': accepted_bids,
            'total_earned': total_earned,
            'average_price': average_price,
        })
    
    return render(request, 'logistics/user_profile.html', context)


@login_required
def notifications_api(request):
    """API для отримання сповіщень (AJAX/HTMX)"""
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if is_htmx:
        # Return HTML for HTMX
        html = render_to_string('logistics/notifications_partial.html', {
            'notifications': notifications,
            'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        }, request=request)
        return HttpResponse(html)
    
    # Return JSON for AJAX
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
