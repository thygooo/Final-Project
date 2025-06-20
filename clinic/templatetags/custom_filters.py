from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):

    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value