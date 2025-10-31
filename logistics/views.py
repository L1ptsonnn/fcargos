from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Route, Bid, Tracking
from .forms import RouteForm, BidForm


@login_required
def routes_list(request):
    """Список маршрутів"""
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user).order_by('-created_at')
    elif request.user.role == 'carrier':
        routes = Route.objects.filter(status='pending').order_by('-created_at')
    else:
        routes = Route.objects.none()
    
    return render(request, 'logistics/routes_list.html', {'routes': routes})


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
            Tracking.objects.create(route=route)
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
    
    context = {
        'route': route,
        'bids': bids,
        'can_bid': can_bid,
        'route_data': {
            'origin': {
                'lat': float(route.origin_lat),
                'lng': float(route.origin_lng),
            },
            'destination': {
                'lat': float(route.destination_lat),
                'lng': float(route.destination_lng),
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
            messages.success(request, 'Ставку успішно створено!')
            return redirect('route_detail', pk=pk)
    else:
        form = BidForm()
    
    return render(request, 'logistics/create_bid.html', {'form': form, 'route': route})


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
    except Tracking.DoesNotExist:
        tracking = Tracking.objects.create(route=route)
    
    context = {
        'route': route,
        'tracking': tracking,
        'route_data': {
            'origin': {
                'lat': float(route.origin_lat),
                'lng': float(route.origin_lng),
            },
            'destination': {
                'lat': float(route.destination_lat),
                'lng': float(route.destination_lng),
            },
            'current': {
                'lat': float(tracking.current_lat) if tracking.current_lat else float(route.origin_lat),
                'lng': float(tracking.current_lng) if tracking.current_lng else float(route.origin_lng),
            }
        }
    }
    return render(request, 'logistics/tracking.html', context)
