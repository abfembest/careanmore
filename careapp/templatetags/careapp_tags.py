from datetime import date, datetime, time

from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def cell(obj, column):
    """Render one list-table cell: choices, booleans, dates, images and relations."""
    if column == '__str__':
        return str(obj)
    if column == 'avatar':  # photo (or initials) with the person's name
        img = (format_html('<img class="avatar-img" src="{}" alt="" loading="lazy">', obj.photo_url) if obj.photo
               else format_html('<span class="avatar-img avatar-img--initials" aria-hidden="true">{}</span>', obj.initials))
        return format_html('<span class="person">{}<span>{}</span></span>', img, obj)
    if column == 'image_src':
        return format_html('<img class="thumb" src="{}" alt="" loading="lazy">', obj.image_src)
    display = getattr(obj, f'get_{column}_display', None)
    value = display() if display else getattr(obj, column)
    if isinstance(value, bool):
        return format_html('<span class="pill pill--{}">{}</span>', 'yes' if value else 'no', 'Yes' if value else 'No')
    if value in (None, ''):
        return format_html('<span class="muted">–</span>')
    if isinstance(value, datetime):
        return value.strftime('%d %b %Y, %H:%M')
    if isinstance(value, date):
        return value.strftime('%d %b %Y')
    if isinstance(value, time):
        return value.strftime('%H:%M')
    if display and column in ('status', 'category', 'role', 'topic', 'contract'):
        return format_html('<span class="pill pill--{}">{}</span>', getattr(obj, column), value)
    return value


@register.filter
def field_kind(field):
    """CSS hook for a bound field's widget type."""
    return field.field.widget.__class__.__name__.lower()
