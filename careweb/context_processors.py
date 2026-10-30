from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse

from .models import Service, SiteSettings


def site_context(request):
    try:
        site = SiteSettings.load()
        nav_services = list(Service.objects.published().only('title', 'slug', 'icon')[:8])
    except (OperationalError, ProgrammingError):  # before migrations have run
        site, nav_services = SiteSettings(), []

    main_nav = [
        {'label': 'Home', 'url': reverse('careweb:home'), 'key': 'home'},
        {'label': 'About us', 'url': reverse('careweb:about'), 'key': 'about'},
        {'label': 'Our care', 'url': reverse('careweb:services'), 'key': 'services'},
        {'label': 'How it works', 'url': reverse('careweb:how_it_works'), 'key': 'how_it_works'},
        {'label': 'Careers', 'url': reverse('careweb:careers'), 'key': 'careers'},
        {'label': 'FAQs', 'url': reverse('careweb:faqs'), 'key': 'faqs'},
        {'label': 'Contact', 'url': reverse('careweb:contact'), 'key': 'contact'},
    ]
    match = getattr(request, 'resolver_match', None)
    current = match.url_name if match else ''
    if current in ('service_detail',):
        current = 'services'
    if current in ('vacancy_detail',):
        current = 'careers'
    if current == 'contact_thanks':
        current = 'contact'
    return {
        'turnstile_site_key': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
        'site': site,
        'main_nav': main_nav,
        'nav_services': nav_services,
        'current_nav': current,
    }
