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
    
@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.simple_tag
def get_entry(dictionary, day, arg2, col=None):
    """
    If called with 3 args: (dictionary, day, col), do 2-key lookup.
    If called with 4 args: (dictionary, day, classroom, col), do 3-key lookup.
    """
    if col is None:
        # 2-key lookup (header)
        return dictionary.get((day, arg2))
    else:
        # 3-key lookup (body)
        return dictionary.get((day, arg2, col))