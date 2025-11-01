from django import template
from logistics.models import Notification

register = template.Library()

@register.simple_tag
def unread_notifications_count(user):
    """Повертає кількість непрочитаних сповіщень для користувача"""
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(user=user, is_read=False).count()

