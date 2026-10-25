from django.core.cache import cache
from django.core.management.base import BaseCommand

from careweb.content import seed
from careweb.models import FAQ, HeroSlide, Service, SiteSettings


class Command(BaseCommand):
    help = 'Load starter content (hero slides, services, FAQs) for the Care Anmore website.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete existing slides, services and FAQs first.')

    def handle(self, *args, **options):
        seed(SiteSettings, HeroSlide, Service, FAQ, reset=options['reset'])
        cache.clear()
        self.stdout.write(self.style.SUCCESS('Care Anmore starter content is in place.'))
