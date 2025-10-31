from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
import json
from logistics.models import Route


def home(request):
    """Головна сторінка з динамічною картою світу"""
    routes = Route.objects.filter(status__in=['pending', 'in_transit']).select_related('company', 'carrier')[:10]
    
    # Формуємо дані для карти
    routes_data = []
    for route in routes:
        routes_data.append({
            'id': route.id,
            'origin': {
                'city': route.origin_city,
                'country': route.origin_country,
                'lat': float(route.origin_lat),
                'lng': float(route.origin_lng),
            },
            'destination': {
                'city': route.destination_city,
                'country': route.destination_country,
                'lat': float(route.destination_lat),
                'lng': float(route.destination_lng),
            },
            'status': route.status,
            'cargo_type': route.cargo_type,
        })
    
    context = {
        'routes': routes,
        'routes_data': json.dumps(routes_data),
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def statistics(request):
    """Сторінка статистики"""
    from logistics.models import Route, Bid
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    context = {}
    
    if request.user.role == 'company':
        routes = Route.objects.filter(company=request.user)
        
        # Статистика по місяцях
        last_6_months = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30*i)
            month_end = month_start - timedelta(days=30)
            month_routes = routes.filter(created_at__gte=month_end, created_at__lt=month_start).count()
            last_6_months.append({
                'month': month_start.strftime('%Y-%m'),
                'count': month_routes
            })
        
        context.update({
            'total_routes': routes.count(),
            'total_spent': routes.filter(status__in=['in_transit', 'delivered']).aggregate(Sum('price'))['price__sum'] or 0,
            'average_price': routes.aggregate(Avg('price'))['price__avg'] or 0,
            'by_status': {
                'pending': routes.filter(status='pending').count(),
                'in_transit': routes.filter(status='in_transit').count(),
                'delivered': routes.filter(status='delivered').count(),
            },
            'monthly_data': last_6_months,
        })
    elif request.user.role == 'carrier':
        bids = Bid.objects.filter(carrier=request.user)
        routes = Route.objects.filter(carrier=request.user)
        
        context.update({
            'total_bids': bids.count(),
            'accepted_rate': (bids.filter(is_accepted=True).count() / bids.count() * 100) if bids.count() > 0 else 0,
            'total_earned': routes.filter(status='delivered').aggregate(Sum('price'))['price__sum'] or 0,
            'average_price': routes.filter(status='delivered').aggregate(Avg('price'))['price__avg'] or 0,
            'completed_routes': routes.filter(status='delivered').count(),
            'active_routes': routes.filter(status='in_transit').count(),
        })
    
    return render(request, 'dashboard/statistics.html', context)


@login_required
def history(request):
    """Історія маршрутів/ставок"""
    from logistics.models import Route, Bid
    
    context = {}
    
    if request.user.role == 'company':
        context['routes'] = Route.objects.filter(company=request.user).order_by('-created_at')
        context['all_statuses'] = ['pending', 'in_transit', 'delivered', 'cancelled']
    elif request.user.role == 'carrier':
        context['bids'] = Bid.objects.filter(carrier=request.user).select_related('route').order_by('-created_at')
        context['my_routes'] = Route.objects.filter(carrier=request.user).order_by('-created_at')
    
    return render(request, 'dashboard/history.html', context)
