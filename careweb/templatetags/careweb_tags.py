from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def icon(name, css_class='', label=''):
    """Render an icon from the inline SVG sprite: {% icon "heart" %}."""
    classes = f'icon {css_class}'.strip()
    if label:
        return format_html(
            '<svg class="{}" role="img" aria-label="{}"><use href="#i-{}"></use></svg>',
            classes, label, name,
        )
    return format_html(
        '<svg class="{}" aria-hidden="true" focusable="false"><use href="#i-{}"></use></svg>',
        classes, name,
    )


@register.filter
def add_class(field, css):
    """Add a CSS class to a bound form field widget."""
    existing = field.field.widget.attrs.get('class', '')
    attrs = {'class': f'{existing} {css}'.strip()}
    if field.errors:
        attrs['aria-invalid'] = 'true'
        attrs['aria-describedby'] = f'{field.id_for_label}-error'
    elif field.help_text:
        attrs['aria-describedby'] = f'{field.id_for_label}-hint'
    return field.as_widget(attrs=attrs)
