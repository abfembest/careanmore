import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .forms import EnquiryForm
from .security import rate_limited
from .models import FAQ, HeroSlide, HomePage, Service, SiteSettings, Vacancy

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'careweb/pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['home'] = HomePage.load()
        ctx['slides'] = HeroSlide.objects.published()
        ctx['services'] = Service.objects.published().filter(is_featured=True)[:6]
        ctx['faqs'] = FAQ.objects.published().filter(show_on_home=True)[:4]
        return ctx


class AboutView(TemplateView):
    template_name = 'careweb/pages/about.html'


class HowItWorksView(TemplateView):
    template_name = 'careweb/pages/how_it_works.html'


class ServiceListView(ListView):
    template_name = 'careweb/services/list.html'
    context_object_name = 'services'

    def get_queryset(self):
        return Service.objects.published()


class ServiceDetailView(DetailView):
    template_name = 'careweb/services/detail.html'
    context_object_name = 'service'

    def get_queryset(self):
        return Service.objects.published()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['related'] = Service.objects.published().exclude(pk=self.object.pk)[:3]
        return ctx


class FAQView(TemplateView):
    template_name = 'careweb/pages/faqs.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        faqs = FAQ.objects.published()
        groups = []
        for key, label in FAQ.CATEGORY_CHOICES:
            items = [f for f in faqs if f.category == key]
            if items:
                groups.append({'key': key, 'label': label, 'items': items})
        ctx['groups'] = groups
        return ctx


class CareersView(ListView):
    template_name = 'careweb/careers/list.html'
    context_object_name = 'vacancies'

    def get_queryset(self):
        return Vacancy.objects.published()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['faqs'] = FAQ.objects.published().filter(category='careers')
        return ctx


class VacancyDetailView(DetailView):
    template_name = 'careweb/careers/detail.html'
    context_object_name = 'vacancy'

    def get_queryset(self):
        return Vacancy.objects.published()


class ContactView(FormView):
    template_name = 'careweb/pages/contact.html'
    form_class = EnquiryForm

    def get_initial(self):
        initial = super().get_initial()
        topic = self.request.GET.get('topic')
        if topic in dict(EnquiryForm.Meta.model.TOPICS):
            initial['topic'] = topic
        service_slug = self.request.GET.get('service')
        if service_slug:
            service = Service.objects.published().filter(slug=service_slug).first()
            if service:
                initial['service'] = service.pk
                initial.setdefault('topic', 'homecare')
        return initial

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'request': self.request}

    def post(self, request, *args, **kwargs):
        limit, window = settings.ENQUIRY_RATE_LIMIT
        if rate_limited(request, 'enquiry', limit, window):
            form = self.get_form()
            form.is_valid()  # keep what the person typed
            form.add_error(None, 'Too many enquiries have been sent from your connection. '
                                 'Please try again later or contact us by phone.')
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        enquiry = form.save(commit=False)
        enquiry.source_page = (self.request.META.get('HTTP_REFERER') or '')[:200]
        enquiry.save()
        self._notify(enquiry)
        self.request.session['enquiry_name'] = enquiry.name.split(' ')[0]
        return redirect('careweb:contact_thanks')

    def form_invalid(self, form):
        if getattr(form, 'is_bot', False):  # don't tell bots why they failed
            return redirect('careweb:contact_thanks')
        messages.error(self.request, 'There is a problem with your enquiry. Check the highlighted fields.')
        return super().form_invalid(form)

    def _notify(self, enquiry):
        recipients = list(settings.ENQUIRY_NOTIFY_EMAILS)
        site = SiteSettings.load()
        if not recipients and site.email:
            recipients = [site.email]
        if not recipients:
            return
        admin_url = self.request.build_absolute_uri(
            reverse('admin:careweb_enquiry_change', args=[enquiry.pk])
        )
        body = (
            f'New website enquiry: {enquiry.get_topic_display()}\n\n'
            f'Name: {enquiry.name}\n'
            f'Preferred contact: {enquiry.get_contact_method_display()}\n'
            f'Email: {enquiry.email or "-"}\nPhone: {enquiry.phone or "-"}\n'
            f'Postcode: {enquiry.postcode or "-"}\n'
            f'Service: {enquiry.service or "Not sure yet"}\n\n'
            f'{enquiry.message}\n\nView in admin: {admin_url}\n'
        )
        try:
            send_mail(f'Website enquiry from {enquiry.name}', body, None, recipients)
        except Exception:  # never lose an enquiry because email failed
            logger.exception('Could not send enquiry notification for enquiry %s', enquiry.pk)


class ContactThanksView(TemplateView):
    template_name = 'careweb/pages/contact_thanks.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['first_name'] = self.request.session.pop('enquiry_name', '')
        return ctx


class LegalView(TemplateView):
    """Privacy, cookies and accessibility statements share one layout."""

    page = None
    PAGES = {
        'privacy': ('careweb/pages/privacy.html', 'Privacy notice'),
        'cookies': ('careweb/pages/cookies.html', 'Cookies'),
        'accessibility': ('careweb/pages/accessibility.html', 'Accessibility statement'),
    }

    def get_template_names(self):
        return [self.PAGES[self.page][0]]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = self.PAGES[self.page][1]
        return ctx


@require_GET
def robots_txt(request):
    lines = [
        'User-agent: *',
        'Disallow: /dashboard/',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')


def error_404(request, exception=None):
    return render(request, 'careweb/errors/404.html', status=404)


def error_500(request):
    return render(request, 'careweb/errors/500.html', status=500)
