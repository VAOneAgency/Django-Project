from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter and return list of stripped strings."""
    return [s.strip() for s in value.split(delimiter) if s.strip()]
