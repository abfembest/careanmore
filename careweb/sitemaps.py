from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Service, Vacancy


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return ['home', 'about', 'services', 'how_it_works', 'faqs', 'careers', 'contact',
                'privacy', 'cookies', 'accessibility']

    def location(self, item):
        return reverse(f'careweb:{item}')


class ServiceSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Service.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class VacancySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        return Vacancy.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {'static': StaticSitemap, 'services': ServiceSitemap, 'vacancies': VacancySitemap}
