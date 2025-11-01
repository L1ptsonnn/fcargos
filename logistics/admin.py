from django.contrib import admin
from .models import Route, Bid, Tracking


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('origin_city', 'destination_city', 'company', 'carrier', 'status', 'price', 'created_at')
    list_filter = ('status', 'created_at', 'cargo_type')
    search_fields = ('origin_city', 'destination_city', 'company__username', 'carrier__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('route', 'carrier', 'proposed_price', 'is_accepted', 'created_at')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('route__origin_city', 'carrier__username')
    ordering = ('-created_at',)


@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    list_display = ('route', 'current_location', 'progress_percent', 'last_update')
    search_fields = ('route__origin_city', 'current_location')
    list_filter = ('last_update', 'progress_percent')
    readonly_fields = ('last_update',)
