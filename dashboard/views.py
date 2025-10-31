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
