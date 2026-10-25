"""Starter content for the Care Anmore website.

Loaded automatically by migration 0002 and by `python manage.py seed_careweb`.
Everything here can be edited afterwards in the Django admin.

Photos are free-to-use images from Unsplash (https://unsplash.com/license),
hotlinked so the project works without downloading media. Replace them with
your own photography by uploading an image in the admin.
"""

U = 'https://images.unsplash.com/{}?auto=format&fit=crop&w=1400&q=80'

HERO_SLIDES = [
    {
        'label': 'Personalised homecare',
        'heading': 'Care that starts with you',
        'text': 'Thoughtful support at home, shaped around your needs, routines and choices.',
        'button_text': 'Start a conversation', 'button_link': '/contact/',
        'secondary_text': 'Explore our care', 'secondary_link': '/our-care/',
        'image_url': U.format('photo-1765896387398-1e1ae8d2eb85'),
        'image_alt': 'A smiling carer leaning towards an older person sitting in a chair',
    },
    {
        'label': 'Independence at home',
        'heading': 'Support that helps you keep doing what you enjoy',
        'text': 'We encourage independence, never taking over the things you would rather do yourself.',
        'button_text': 'How it works', 'button_link': '/how-it-works/',
        'secondary_text': 'Talk to our team', 'secondary_link': '/contact/',
        'image_url': U.format('photo-1773227055624-07b515ba87c5'),
        'image_alt': 'A carer walking alongside an older woman using a walking frame',
    },
    {
        'label': 'Companionship',
        'heading': 'Good company, conversation and connection',
        'text': 'Friendly visits that help you stay in touch with the interests and people that matter to you.',
        'button_text': 'Ask about companionship', 'button_link': '/our-care/companionship/',
        'secondary_text': 'About us', 'secondary_link': '/about/',
        'image_url': U.format('photo-1765896387377-e293914d1e69'),
        'image_alt': 'Two women laughing together indoors',
    },
]

SERVICES = [
    {
        'title': 'Personal care', 'slug': 'personal-care', 'icon': 'heart',
        'summary': 'Respectful assistance with personal routines, with privacy and dignity always at the centre.',
        'intro': 'Personal care is about helping you feel comfortable and confident in your own home, in the way you prefer.',
        'body': (
            'We take time to understand how you like things done, from the order of your morning routine to the '
            'products you use. Support is agreed with you, and we explain what we are doing as we go.\n\n'
            'Your privacy and dignity matter. Where possible we encourage you to do as much as you would like '
            'for yourself, with support available for the parts that are harder.'
        ),
        'includes': 'Washing, bathing and showering\nDressing and grooming\nOral care and shaving\nContinence support\nSupport with mobility around the home',
        'image_url': U.format('photo-1765896387387-0538bc9f997e'),
        'image_alt': 'A carer smiling with an older person in a bright room',
    },
    {
        'title': 'Daily living', 'slug': 'daily-living', 'icon': 'sun',
        'summary': 'Practical help with agreed everyday tasks, meals and routines that matter to you.',
        'intro': 'Small tasks can make a big difference to how a day feels. We help with the everyday things you have agreed with us.',
        'body': (
            'That might mean preparing a meal you enjoy, keeping the kitchen tidy, or helping you stay on top of '
            'household routines. We work at your pace and follow the plan we have agreed together.\n\n'
            'If your needs or circumstances change, we talk with you, and with your family or representative '
            'if you would like us to, before anything is adjusted.'
        ),
        'includes': 'Meal preparation and hydration\nLight housework and laundry\nShopping and errands\nPrompting with medication, where agreed\nKeeping to routines that matter to you',
        'image_url': U.format('photo-1525336778665-96f9a12c5c4f'),
        'image_alt': 'A person holding a white ceramic teacup',
    },
    {
        'title': 'Companionship', 'slug': 'companionship', 'icon': 'users',
        'summary': 'Friendly social contact and support to maintain interests, relationships and connection.',
        'intro': 'Companionship visits are about company, conversation and staying connected to the things you love.',
        'body': (
            'We can spend time chatting over a cup of tea, help you get out to a local group, or simply be there '
            'while you enjoy a hobby. Visits are shaped around your interests.\n\n'
            'For families who live further away, companionship can offer reassurance that someone is checking in '
            'regularly and keeping communication open.'
        ),
        'includes': 'Conversation and company at home\nSupport with hobbies and interests\nAccompanied trips out\nHelp staying in touch with family and friends\nEncouragement to join local activities',
        'image_url': U.format('photo-1762955913084-96ea3f986468'),
        'image_alt': 'A carer sitting with older women enjoying a knitting activity',
    },
    {
        'title': 'Support at home', 'slug': 'support-at-home', 'icon': 'home',
        'summary': 'Care planning that considers your home environment, routines and personal goals.',
        'intro': 'Your home is part of your care. We think about how it works for you and what would make day-to-day life easier.',
        'body': (
            'As part of planning, we look at your home environment and routines with you, so support fits '
            'naturally into how you live and helps you stay safe.\n\n'
            'Where it would help, we can signpost you to other services such as equipment, adaptations or '
            'community support.'
        ),
        'includes': 'Home environment considered in planning\nSupport fitted around your routines\nSignposting to other local services\nRegular reviews of what is working',
        'image_url': U.format('photo-1581579438930-a0269719fde7'),
        'image_alt': 'An older woman at home holding a mug',
    },
    {
        'title': 'Planned visits', 'slug': 'planned-visits', 'icon': 'clock',
        'summary': 'Support arrangements discussed around assessed needs, visit timing and availability.',
        'intro': 'Visits are planned around your assessed needs and the times of day that work best for you.',
        'body': (
            'We discuss how often you would like visits, how long they should be and what each one is for. '
            'Arrangements depend on an individual assessment and our availability in your area.\n\n'
            'We aim to communicate clearly about visit times and let you know if anything needs to change.'
        ),
        'includes': 'Visit times agreed with you\nVisit length based on assessed needs\nClear communication about changes\nRegular reviews of your plan',
        'image_url': U.format('photo-1543333995-a78aea2eee50'),
        'image_alt': 'A woman walking beside a person in a wheelchair outdoors',
    },
    {
        'title': 'Individual support', 'slug': 'individual-support', 'icon': 'sparkle',
        'summary': 'We listen to communication preferences, strengths, culture and the outcomes important to each person.',
        'intro': 'No two people are the same. Individual support starts with understanding who you are and what matters to you.',
        'body': (
            'We take account of your communication preferences, culture, faith, strengths and personal goals, '
            'and build these into the way support is provided.\n\n'
            'You, and anyone you choose to involve, have a voice in how your support is planned and reviewed.'
        ),
        'includes': 'Communication that suits you\nRespect for culture, faith and identity\nSupport built around your goals\nFamily or representative involvement if you choose',
        'image_url': U.format('photo-1762955911431-4c44c7c3f408'),
        'image_alt': 'A carer helping an older couple with a colouring activity',
    },
]

FAQS = [
    ('getting-started', 'How do I start an enquiry?',
     'Use the enquiry form or contact the team. We will talk with you about what you are looking for, answer your questions and explain the next steps.', True),
    ('getting-started', 'Is an enquiry the same as booking care?',
     'No. An enquiry starts a conversation. Any support must be discussed and assessed before arrangements are agreed.', True),
    ('getting-started', 'Which areas do you cover?',
     'We serve Peterborough and surrounding areas, subject to confirmed coverage. Include your postcode in your enquiry and we will let you know.', True),
    ('care', 'Will I have a say in how my care is provided?',
     'Yes. We take time to understand your preferences, routines and goals, and agree support together wherever possible.', True),
    ('care', 'What happens if my needs change?',
     'We communicate clearly when needs or circumstances change and review your support with you, and with your family or representative if you would like.', False),
    ('families', 'Can I make an enquiry on behalf of a family member?',
     'Yes. Choose "Family or representative enquiry" on the form. Where possible we will involve the person who would receive support in any conversation about their care.', False),
    ('families', 'Can professionals make a referral?',
     'Yes. Choose "Professional referral" on the enquiry form and the team will be in touch to discuss the next steps.', False),
    ('careers', 'Do I need previous care experience?',
     'Not always. We value kindness, reliability and good communication. Ask us about current opportunities and the support available to new team members.', False),
]

SITE_SETTINGS = {
    'organisation_name': 'Care Anmore Ltd',
    'tagline': 'Care that starts with you',
    'service_area': 'Peterborough and surrounding areas',
    'show_preview_banner': True,
}


def seed(SiteSettings, HeroSlide, Service, FAQ, reset=False):
    """Create starter content. Works with real or historical (migration) models."""
    if reset:
        HeroSlide.objects.all().delete()
        Service.objects.all().delete()
        FAQ.objects.all().delete()

    if not SiteSettings.objects.filter(pk=1).exists():
        SiteSettings.objects.create(pk=1, **SITE_SETTINGS)

    if not HeroSlide.objects.exists():
        for i, slide in enumerate(HERO_SLIDES):
            HeroSlide.objects.create(order=i, **slide)

    for i, svc in enumerate(SERVICES):
        Service.objects.get_or_create(slug=svc['slug'], defaults={**svc, 'order': i})

    if not FAQ.objects.exists():
        for i, (cat, q, a, home) in enumerate(FAQS):
            FAQ.objects.create(category=cat, question=q, answer=a, show_on_home=home, order=i)
