"""Dashboard sections. Each entry gives a model full list/create/edit/delete pages.

To add a section, add one entry here: no new views, URLs or templates needed.
"""
from careweb.models import FAQ, Enquiry, HeroSlide, HomePage, Service, SiteSettings, Vacancy

from .models import ServiceUser, Shift, StaffMember

IMAGE_FIELDS = ['image', 'image_url', 'image_alt']

SECTIONS = {
    # ---- Care operations ----
    'service-users': dict(
        model=ServiceUser, title='Service users', icon='users', group='care', area='service_users',
        fields=['first_name', 'last_name', 'photo', 'status', 'service', 'weekly_hours', 'start_date',
                'postcode', 'phone', 'key_contact', 'notes'],
        columns=['avatar', 'status', 'service', 'weekly_hours', 'postcode'],
        search=['first_name', 'last_name', 'postcode'], filter='status', related=['service'],
    ),
    'staff': dict(
        model=StaffMember, title='Staff', icon='briefcase', group='care', area='staff',
        fields=['first_name', 'last_name', 'role', 'status', 'start_date', 'email', 'phone', 'notes'],
        columns=['__str__', 'role', 'status', 'start_date', 'phone'],
        search=['first_name', 'last_name', 'email'], filter='status',
    ),
    'shifts': dict(
        model=Shift, title='Shifts', icon='calendar', group='care', area='shifts',
        fields=['service_user', 'staff', 'date', 'start_time', 'end_time', 'status', 'notes'],
        columns=['date', 'start_time', 'end_time', 'service_user', 'staff', 'hours', 'status'],
        search=['service_user__first_name', 'service_user__last_name', 'staff__first_name', 'staff__last_name'],
        filter='status', related=['service_user', 'staff'],
    ),
    # ---- Website ----
    'enquiries': dict(
        model=Enquiry, title='Enquiries', icon='mail', group='website', area='enquiries', can_create=False,
        fields=['status', 'staff_notes'],
        details=['name', 'contact_method', 'email', 'phone', 'postcode', 'topic', 'service', 'message', 'created_at'],
        columns=['created_at', 'name', 'topic', 'contact_method', 'status'],
        search=['name', 'email', 'phone', 'postcode', 'message'], filter='status', related=['service'],
    ),
    'hero-slides': dict(
        model=HeroSlide, title='Hero slides', icon='sparkle', group='site', area='site',
        fields=['label', 'heading', 'text', 'button_text', 'button_link', 'secondary_text',
                'secondary_link', *IMAGE_FIELDS, 'order', 'is_published'],
        columns=['image_src', 'heading', 'order', 'is_published'], search=['heading', 'text'],
    ),
    'services': dict(
        model=Service, title='Services', icon='heart', group='site', area='site',
        fields=['title', 'slug', 'icon', 'summary', 'intro', 'body', 'includes', *IMAGE_FIELDS,
                'order', 'is_featured', 'is_published', 'meta_description'],
        columns=['image_src', 'title', 'order', 'is_featured', 'is_published'], search=['title', 'summary'],
    ),
    'faqs': dict(
        model=FAQ, title='FAQs', icon='chat', group='site', area='site',
        fields=['question', 'answer', 'category', 'order', 'show_on_home', 'is_published'],
        columns=['question', 'category', 'show_on_home', 'is_published'], search=['question', 'answer'],
        filter='category',
    ),
    'vacancies': dict(
        model=Vacancy, title='Careers', icon='briefcase', group='site', area='site',
        fields=['title', 'slug', 'location', 'contract', 'salary', 'summary', 'description',
                'requirements', 'closing_date', 'is_published'],
        columns=['title', 'location', 'contract', 'closing_date', 'is_published'], search=['title'],
    ),
}

# Single-row content pages edited through one form each (permission area: 'site').
SETTINGS_PAGES = {
    'general': dict(
        model=SiteSettings, title='General', icon='home',
        fields=['organisation_name', 'tagline', 'phone', 'email', 'address', 'service_area', 'opening_hours',
                'company_number', 'cqc_location_id', 'show_preview_banner'],
    ),
    'branding': dict(model=SiteSettings, title='Logos & branding', icon='sparkle',
                     fields=['logo', 'footer_logo', 'favicon']),
    'home-page': dict(
        model=HomePage, title='Home page', icon='home',
        fields=['trust_1', 'trust_2', 'trust_3', 'services_title', 'services_intro', 'approach_label',
                'approach_title', 'approach_lead', 'approach_body', *IMAGE_FIELDS, 'approach_badge_title',
                'approach_badge_text', 'steps_title', 'steps_intro', 'area_text', 'faq_title', 'faq_intro',
                'cta_title', 'cta_text'],
    ),
    'footer': dict(
        model=SiteSettings, title='Footer', icon='clipboard',
        fields=['footer_text', 'footer_disclaimer', 'show_help_strip', 'facebook_url', 'linkedin_url',
                'instagram_url'],
    ),
}

# Order of the "Site settings" submenu: (kind, key)
SITE_MENU = [('settings', 'general'), ('settings', 'branding'), ('settings', 'home-page'),
             ('section', 'hero-slides'), ('section', 'services'), ('section', 'faqs'),
             ('section', 'vacancies'), ('settings', 'footer')]
