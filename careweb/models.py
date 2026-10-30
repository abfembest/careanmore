"""Content and enquiry models for the Care Anmore public website.

Everything shown on the public site (hero slides, services, FAQs, vacancies,
contact details) is editable from the Django admin so the site can grow
without code changes.
"""
from django.core.cache import cache
from django.core.validators import FileExtensionValidator
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify

IMAGE_VALIDATOR = FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'avif'])
LOGO_VALIDATOR = FileExtensionValidator(['svg', 'png', 'jpg', 'jpeg', 'webp', 'ico'])

ICON_CHOICES = [
    ('heart', 'Heart'),
    ('sun', 'Sun'),
    ('users', 'People'),
    ('home', 'Home'),
    ('clock', 'Clock'),
    ('sparkle', 'Sparkle'),
    ('hand', 'Helping hand'),
    ('shield', 'Shield'),
    ('chat', 'Conversation'),
    ('leaf', 'Leaf'),
    ('clipboard', 'Clipboard'),
    ('meal', 'Meal'),
]


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class ImageMixin(models.Model):
    """An uploaded image wins; otherwise an external URL; otherwise a static fallback."""

    image = models.FileField(
        upload_to='careweb/%Y/%m/', blank=True, validators=[IMAGE_VALIDATOR],
        help_text='Upload a photo (JPG, PNG or WebP). Takes priority over the image URL.',
    )
    image_url = models.URLField(
        'image URL', blank=True, max_length=500,
        help_text='Optional external image (e.g. a licensed Unsplash photo).',
    )
    image_alt = models.CharField(
        'image description', max_length=200, blank=True,
        help_text='Describe the image for people using screen readers.',
    )

    FALLBACK_IMAGE = 'careweb/img/fallback.svg'

    class Meta:
        abstract = True

    @property
    def image_src(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return static(self.FALLBACK_IMAGE)


class SingletonModel(TimeStampedModel):
    """A table with exactly one row (pk=1), cached for fast reads."""

    class Meta:
        abstract = True

    @classmethod
    def cache_key(cls):
        return f'careweb:singleton:{cls._meta.model_name}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.cache_key())

    def delete(self, *args, **kwargs):  # the single row is never deleted
        return None

    @classmethod
    def load(cls):
        obj = cache.get(cls.cache_key())
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls.cache_key(), obj, 60 * 15)
        return obj


class SiteSettings(SingletonModel):
    """Single row holding organisation-wide details shown across the site."""

    organisation_name = models.CharField(max_length=120, default='Care Anmore Ltd')
    tagline = models.CharField(max_length=200, default='Care that starts with you')
    phone = models.CharField(max_length=40, blank=True, help_text='Leave blank until verified.')
    email = models.EmailField(blank=True, help_text='Leave blank until verified.')
    address = models.TextField(blank=True)
    service_area = models.CharField(max_length=200, default='Peterborough and surrounding areas')
    opening_hours = models.CharField(max_length=200, blank=True, help_text='e.g. Monday to Friday, 9am to 5pm')
    company_number = models.CharField(max_length=40, blank=True)
    cqc_location_id = models.CharField(
        'CQC location ID', max_length=40, blank=True,
        help_text='Only add once registration is confirmed. Shows a link to the CQC profile.',
    )
    show_preview_banner = models.BooleanField(
        default=True,
        help_text='Shows a notice that content is awaiting final approval. Turn off at launch.',
    )
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    # Branding
    logo = models.FileField(upload_to='branding/', blank=True, validators=[LOGO_VALIDATOR],
                            help_text='Header logo (SVG or PNG, about 440×120).')
    footer_logo = models.FileField(upload_to='branding/', blank=True, validators=[LOGO_VALIDATOR],
                                   help_text='Optional. Uses the header logo if empty.')
    favicon = models.FileField(upload_to='branding/', blank=True, validators=[LOGO_VALIDATOR],
                               help_text='Browser tab icon (square SVG or PNG).')

    # Footer
    footer_text = models.CharField(max_length=240, default='Personalised homecare support shaped around the person.')
    footer_disclaimer = models.TextField(
        blank=True,
        default=('Website preview content. Final service descriptions, contact details, privacy information '
                 'and any regulatory statements must be verified and approved before publication. Do not treat '
                 'this preview as confirmation of registration or service availability.'),
        help_text='Shown at the bottom of every page while the preview banner is on.',
    )
    show_help_strip = models.BooleanField('show urgent help strip', default=True,
                                          help_text='The 999 / NHS 111 notice above the footer.')

    class Meta:
        verbose_name = 'site settings'
        verbose_name_plural = 'site settings'

    def __str__(self):
        return 'Site settings'

    def _file_or_static(self, field, fallback):
        f = getattr(self, field)
        return f.url if f else static(fallback)

    @property
    def logo_src(self):
        return self._file_or_static('logo', 'careweb/img/logo.svg')

    @property
    def footer_logo_src(self):
        return self.footer_logo.url if self.footer_logo else self.logo_src

    @property
    def favicon_src(self):
        return self._file_or_static('favicon', 'careweb/img/favicon.svg')

    @property
    def phone_href(self):
        return 'tel:' + ''.join(ch for ch in self.phone if ch.isdigit() or ch == '+')

    @property
    def cqc_url(self):
        if self.cqc_location_id:
            return f'https://www.cqc.org.uk/location/{self.cqc_location_id}'
        return ''


class HomePage(ImageMixin, SingletonModel):
    """Editable text for the home page sections (the hero uses HeroSlide)."""

    FALLBACK_IMAGE = 'careweb/img/fallback.svg'

    trust_1 = models.CharField(max_length=80, default='Care shaped around the individual')
    trust_2 = models.CharField(max_length=80, default='Respect for dignity and choice')
    trust_3 = models.CharField(max_length=80, default='Clear communication with you')
    services_title = models.CharField(max_length=120, default='Support for everyday life')
    services_intro = models.TextField(default=(
        'We will discuss your circumstances and preferences to understand what support may be appropriate. '
        'The final care arrangement depends on an individual assessment and confirmed service scope.'))
    approach_label = models.CharField(max_length=40, default='Our approach')
    approach_title = models.CharField(max_length=120, default='You’re a person first. Always.')
    approach_lead = models.CharField(max_length=200, default='Good care is built on listening, trust and respect.')
    approach_body = models.TextField(default=(
        'We want people to have a voice in how support is provided. That means taking time to understand '
        'preferences, explaining choices clearly and agreeing support together wherever possible.\n\n'
        'Our aim is to encourage independence, not to take over tasks unnecessarily, and to communicate '
        'clearly when needs or circumstances change.'), help_text='Separate paragraphs with a blank line.')
    approach_badge_title = models.CharField(max_length=60, default='Support with dignity.')
    approach_badge_text = models.CharField(max_length=120, default='Respect, choice and wellbeing guide every visit.')
    steps_title = models.CharField(max_length=120, default='A clear, thoughtful first step')
    steps_intro = models.TextField(default=(
        'We begin with a conversation. No two people are the same, so any proposed support must be '
        'discussed and assessed before arrangements are agreed.'))
    area_text = models.CharField(max_length=240, default=(
        'Coverage is confirmed individually. Add your postcode to your enquiry and we will let you know '
        'whether we can help.'))
    faq_title = models.CharField(max_length=120, default='Questions people often ask')
    faq_intro = models.CharField(max_length=240, default=(
        'If you cannot find what you are looking for, get in touch and we will be happy to help.'))
    cta_title = models.CharField(max_length=120, default='Let’s start with a conversation')
    cta_text = models.CharField(max_length=300, default=(
        'Tell us what you are looking for and how you would like to be contacted. We will explain the next '
        'steps in clear language.'))

    class Meta:
        verbose_name = 'home page'
        verbose_name_plural = 'home page'

    def __str__(self):
        return 'Home page'

    @property
    def approach_paragraphs(self):
        return [p.strip() for p in self.approach_body.split('\n\n') if p.strip()]


class HeroSlide(ImageMixin, TimeStampedModel):
    heading = models.CharField(max_length=120)
    text = models.TextField(max_length=400)
    label = models.CharField(max_length=60, blank=True, help_text='Short tag above the heading.')
    button_text = models.CharField(max_length=40, default='Start a conversation')
    button_link = models.CharField(max_length=200, default='/contact/')
    secondary_text = models.CharField(max_length=40, blank=True)
    secondary_link = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    objects = OrderedQuerySet.as_manager()

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.heading


class Service(ImageMixin, TimeStampedModel):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='heart')
    summary = models.CharField(max_length=240)
    intro = models.TextField(blank=True, help_text='Opening paragraph on the service page.')
    body = models.TextField(blank=True, help_text='Separate paragraphs with a blank line.')
    includes = models.TextField(
        'what support can include', blank=True,
        help_text='One item per line. Shown as a checklist.',
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_featured = models.BooleanField(default=True, help_text='Show on the home page.')
    is_published = models.BooleanField(default=True)
    meta_description = models.CharField(max_length=160, blank=True)

    objects = OrderedQuerySet.as_manager()

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('careweb:service_detail', kwargs={'slug': self.slug})

    @property
    def includes_list(self):
        return [line.strip() for line in self.includes.splitlines() if line.strip()]

    @property
    def body_paragraphs(self):
        return [p.strip() for p in self.body.split('\n\n') if p.strip()]


class FAQ(TimeStampedModel):
    CATEGORY_CHOICES = [
        ('getting-started', 'Getting started'),
        ('care', 'About our care'),
        ('families', 'Families and representatives'),
        ('careers', 'Careers'),
    ]
    question = models.CharField(max_length=200)
    answer = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='getting-started')
    order = models.PositiveSmallIntegerField(default=0)
    show_on_home = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    objects = OrderedQuerySet.as_manager()

    class Meta:
        ordering = ['category', 'order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class Vacancy(TimeStampedModel):
    CONTRACT_CHOICES = [
        ('full-time', 'Full time'),
        ('part-time', 'Part time'),
        ('flexible', 'Flexible hours'),
        ('bank', 'Bank / relief'),
    ]
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=130, unique=True, blank=True)
    location = models.CharField(max_length=120, default='Peterborough')
    contract = models.CharField(max_length=20, choices=CONTRACT_CHOICES, default='part-time')
    salary = models.CharField(max_length=80, blank=True)
    summary = models.CharField(max_length=240)
    description = models.TextField(help_text='Separate paragraphs with a blank line.')
    requirements = models.TextField(blank=True, help_text='One item per line.')
    closing_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True)

    objects = OrderedQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'vacancies'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('careweb:vacancy_detail', kwargs={'slug': self.slug})

    @property
    def requirements_list(self):
        return [line.strip() for line in self.requirements.splitlines() if line.strip()]

    @property
    def description_paragraphs(self):
        return [p.strip() for p in self.description.split('\n\n') if p.strip()]


class Enquiry(TimeStampedModel):
    CONTACT_METHODS = [('phone', 'Phone'), ('email', 'Email')]
    TOPICS = [
        ('homecare', 'Homecare enquiry'),
        ('family', 'Family or representative enquiry'),
        ('referral', 'Professional referral'),
        ('careers', 'Careers enquiry'),
        ('other', 'Other question'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    ]

    name = models.CharField('your name', max_length=120)
    contact_method = models.CharField('preferred contact method', max_length=10, choices=CONTACT_METHODS)
    email = models.EmailField('email address', blank=True)
    phone = models.CharField('phone number', max_length=40, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    topic = models.CharField('what would you like to discuss?', max_length=20, choices=TOPICS)
    service = models.ForeignKey(
        Service, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='service you are interested in',
    )
    message = models.TextField('short message', blank=True, max_length=2000)
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='new')
    staff_notes = models.TextField(blank=True)
    source_page = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'enquiries'

    def __str__(self):
        return f'{self.name} — {self.get_topic_display()}'
