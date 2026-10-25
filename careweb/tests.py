from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Enquiry, HeroSlide, Service, SiteSettings, Vacancy


class PageTests(TestCase):
    """Starter content is loaded by migration 0002, so pages have real data."""

    def test_public_pages_load(self):
        names = ['home', 'about', 'services', 'how_it_works', 'faqs', 'careers',
                 'contact', 'privacy', 'cookies', 'accessibility']
        for name in names:
            with self.subTest(page=name):
                response = self.client.get(reverse(f'careweb:{name}'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Skip to main content')

    def test_home_shows_carousel_and_services(self):
        response = self.client.get(reverse('careweb:home'))
        self.assertEqual(HeroSlide.objects.count(), 3)
        self.assertContains(response, 'data-carousel')
        self.assertContains(response, 'Care that starts with you')
        self.assertContains(response, 'Personal care')

    def test_service_detail(self):
        service = Service.objects.get(slug='personal-care')
        response = self.client.get(service.get_absolute_url())
        self.assertContains(response, 'What support can include')
        self.assertContains(response, '?service=personal-care')

    def test_unpublished_service_404(self):
        Service.objects.filter(slug='personal-care').update(is_published=False)
        response = self.client.get(reverse('careweb:service_detail', args=['personal-care']))
        self.assertEqual(response.status_code, 404)

    def test_vacancy_detail(self):
        job = Vacancy.objects.create(title='Care assistant', summary='Join us', description='Para one.\n\nPara two.')
        response = self.client.get(job.get_absolute_url())
        self.assertContains(response, 'Para two.')

    def test_sitemap_and_robots(self):
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)
        robots = self.client.get('/robots.txt')
        self.assertContains(robots, 'Disallow: /admin/')

    def test_site_settings_singleton(self):
        s = SiteSettings.load()
        s.phone = '01733 000000'
        s.save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        response = self.client.get(reverse('careweb:contact'))
        self.assertContains(response, 'tel:01733000000')


class EnquiryTests(TestCase):
    def valid_data(self, **extra):
        data = {
            'name': 'Jane Smith', 'contact_method': 'email', 'email': 'jane@example.com',
            'phone': '', 'postcode': 'PE1 1AA', 'topic': 'homecare', 'service': '',
            'message': 'I would like to know more.', 'consent': 'on', 'website': '',
        }
        data.update(extra)
        return data

    @override_settings(ENQUIRY_NOTIFY_EMAILS=['team@example.com'])
    def test_valid_enquiry_saved_and_emailed(self):
        response = self.client.post(reverse('careweb:contact'), self.valid_data())
        self.assertRedirects(response, reverse('careweb:contact_thanks'), fetch_redirect_response=False)
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        thanks = self.client.get(reverse('careweb:contact_thanks'))
        self.assertContains(thanks, 'thank you Jane')

    def test_email_required_when_email_chosen(self):
        response = self.client.post(reverse('careweb:contact'), self.valid_data(email=''))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There is a problem')
        self.assertContains(response, 'Enter an email address')
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_consent_required(self):
        data = self.valid_data()
        data.pop('consent')
        response = self.client.post(reverse('careweb:contact'), data)
        self.assertContains(response, 'Confirm you have read the privacy information')

    def test_honeypot_blocks_bots(self):
        self.client.post(reverse('careweb:contact'), self.valid_data(website='spam'))
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_topic_and_service_prefill(self):
        response = self.client.get(reverse('careweb:contact') + '?service=companionship')
        service = Service.objects.get(slug='companionship')
        self.assertContains(response, f'value="{service.pk}" selected')
