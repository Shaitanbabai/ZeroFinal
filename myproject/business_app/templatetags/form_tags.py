from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter
def create_range(value):
    try:
        return range(int(value))
    except (TypeError, ValueError):
        return []


@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (ValueError, TypeError):
        return ''


@register.filter
def in_list(value, the_list):
    return value in the_list


@register.filter(name='currency')
def currency(value):
    try:
        # Используем пробел как разделитель тысяч и добавляем символ рубля
        return "{:,.2f} ₽".format(float(value)).replace(',', ' ')
    except (ValueError, TypeError):
        return value
