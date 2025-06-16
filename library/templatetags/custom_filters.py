from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return '' 
    
@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return '' 