from django.core.cache import cache

from careweb.models import Enquiry

from .permissions import allowed
from .registry import SECTIONS, SETTINGS_PAGES, SITE_MENU


def dashboard_nav(request):
    """Sidebar data, only for dashboard pages, filtered by the user's role."""
    match = getattr(request, 'resolver_match', None)
    if not match or match.app_name != 'careapp' or not request.user.is_authenticated:
        return {}
    perms = allowed(request.user)
    new_count = 0
    if 'view' in perms['enquiries']:
        new_count = cache.get('careapp:new-enquiries')
        if new_count is None:
            new_count = Enquiry.objects.filter(status='new').count()
            cache.set('careapp:new-enquiries', new_count, 30)
    site_menu = []
    if 'view' in perms['site']:
        for kind, key in SITE_MENU:
            cfg = SETTINGS_PAGES[key] if kind == 'settings' else SECTIONS[key]
            url_name = 'careapp:settings' if kind == 'settings' else 'careapp:section_list'
            site_menu.append({'title': cfg['title'], 'icon': cfg['icon'], 'url_name': url_name, 'key': key})
    kw = match.kwargs
    return {
        'perms_for': perms,
        'nav_care': [(k, SECTIONS[k]) for k in ('service-users', 'staff', 'shifts') if 'view' in perms[SECTIONS[k]['area']]],
        'nav_site': site_menu,
        'nav_current': kw.get('section') or kw.get('page') or match.url_name,
        'nav_site_open': kw.get('page') in SETTINGS_PAGES or kw.get('section') in {k for _, k in SITE_MENU},
        'new_enquiries': new_count,
    }
