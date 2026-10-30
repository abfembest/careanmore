from datetime import timedelta
from functools import reduce
from operator import or_

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db import models
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.forms import modelform_factory
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from careweb.models import Enquiry, SiteSettings

from .models import OnboardingTask, ServiceUser, Shift, StaffMember
from .permissions import can
from .registry import SECTIONS, SETTINGS_PAGES

DASHBOARD_CACHE_KEY = 'careapp:dashboard-stats'


class SecureLoginView(LoginView):
    template_name = 'careapp/login.html'
    redirect_authenticated_user = True

    def get_form_class(self):
        from .forms import SecureLoginForm
        return SecureLoginForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['site'] = SiteSettings.load()  # LoginView sets its own 'site'; use the brand settings
        return ctx


class AccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Checks the permission matrix: `action` for reading, `write_action` for POSTs."""
    login_url = 'careapp:login'
    area = None
    action = 'view'
    write_action = 'change'

    def get_area(self):
        return self.area

    def test_func(self):
        safe = self.request.method in ('GET', 'HEAD', 'OPTIONS')
        return can(self.request.user, self.get_area(), self.action if safe else self.write_action)


def _formfield(field, **kwargs):
    """Native date/time pickers and roomy text areas for every dashboard form."""
    if isinstance(field, models.DateTimeField):
        kwargs['widget'] = forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
    elif isinstance(field, models.DateField):
        kwargs['widget'] = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
    elif isinstance(field, models.TimeField):
        kwargs['widget'] = forms.TimeInput(attrs={'type': 'time'}, format='%H:%M')
    elif isinstance(field, models.TextField):
        kwargs['widget'] = forms.Textarea(attrs={'rows': 4})
    return field.formfield(**kwargs)


def build_form(model, fields):
    return modelform_factory(model, fields=fields, formfield_callback=_formfield)


# --------------------------------------------------------------------------
# Generic section pages (driven by registry.SECTIONS)
# --------------------------------------------------------------------------
class SectionMixin(AccessMixin):
    paginate_by = 20

    def get_area(self):
        return self.cfg['area']

    def dispatch(self, request, *args, **kwargs):
        self.key = kwargs['section']
        self.cfg = SECTIONS.get(self.key)
        if not self.cfg:
            raise Http404('Unknown section')
        self.model = self.cfg['model']
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related(*self.cfg.get('related', []))

    def get_form_class(self):
        return build_form(self.model, self.cfg['fields'])

    def get_success_url(self):
        return reverse('careapp:section_list', args=[self.key])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user, area = self.request.user, self.cfg['area']
        ctx.update(section=self.cfg, section_key=self.key, page_title=self.cfg['title'],
                   can_create=self.cfg.get('can_create', True) and can(user, area, 'add'),
                   can_edit=can(user, area, 'change'), can_delete=can(user, area, 'delete'),
                   singular=self.model._meta.verbose_name)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Saved “{form.instance}”.')
        cache.delete(DASHBOARD_CACHE_KEY)
        return super().form_valid(form)


class SectionListView(SectionMixin, ListView):
    template_name = 'careapp/list.html'
    write_action = 'view'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q and self.cfg.get('search'):
            qs = qs.filter(reduce(or_, (Q(**{f'{f}__icontains': q}) for f in self.cfg['search'])))
        value = self.request.GET.get('filter')
        if value and self.cfg.get('filter'):
            qs = qs.filter(**{self.cfg['filter']: value})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.model._meta
        ctx['headers'] = [
            'Name' if c in ('__str__', 'avatar') else 'Image' if c == 'image_src'
            else str(meta.get_field(c).verbose_name).capitalize() for c in self.cfg['columns']
        ]
        if self.cfg.get('filter'):
            ctx['filter_choices'] = meta.get_field(self.cfg['filter']).choices
        ctx['q'] = self.request.GET.get('q', '')
        ctx['active_filter'] = self.request.GET.get('filter', '')
        return ctx


class SectionCreateView(SectionMixin, CreateView):
    template_name = 'careapp/form.html'
    action = write_action = 'add'

    def dispatch(self, request, *args, **kwargs):
        if not SECTIONS.get(kwargs['section'], {}).get('can_create', True):
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class SectionUpdateView(SectionMixin, UpdateView):
    template_name = 'careapp/form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not can(self.request.user, self.cfg['area'], 'change'):  # read-only view
            for field in form.fields.values():
                field.disabled = True
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['details'] = [
            (str(self.model._meta.get_field(f).verbose_name).capitalize(),
             getattr(self.object, f'get_{f}_display', lambda f=f: getattr(self.object, f))())
            for f in self.cfg.get('details', [])
        ]
        return ctx


class SectionDeleteView(SectionMixin, DeleteView):
    template_name = 'careapp/confirm_delete.html'
    action = write_action = 'delete'

    def get_form_class(self):
        return forms.Form

    def form_valid(self, form):
        messages.success(self.request, f'Deleted “{self.object}”.')
        cache.delete(DASHBOARD_CACHE_KEY)
        return DeleteView.form_valid(self, form)


class SettingsView(AccessMixin, UpdateView):
    """Edit one group of fields on a single-row model (site settings, home page)."""
    template_name = 'careapp/form.html'
    area = 'site'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not can(self.request.user, 'site', 'change'):
            for field in form.fields.values():
                field.disabled = True
        return form

    def dispatch(self, request, *args, **kwargs):
        self.key = kwargs['page']
        self.cfg = SETTINGS_PAGES.get(self.key)
        if not self.cfg:
            raise Http404('Unknown settings page')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.cfg['model'].objects.get_or_create(pk=1)[0]

    def get_form_class(self):
        return build_form(self.cfg['model'], self.cfg['fields'])

    def get_success_url(self):
        return reverse('careapp:settings', args=[self.key])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(section=self.cfg, settings_key=self.key, page_title=self.cfg['title'], is_settings=True,
                   can_edit=can(self.request.user, 'site', 'change'))
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'{self.cfg["title"]} updated. Changes are live on the website.')
        return super().form_valid(form)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def _series(rows, keys, label_fmt):
    lookup = {r['period'].date() if hasattr(r['period'], 'date') else r['period']: float(r['value'] or 0) for r in rows}
    return {'labels': [k.strftime(label_fmt) for k in keys], 'values': [lookup.get(k, 0) for k in keys]}


def dashboard_stats():
    stats = cache.get(DASHBOARD_CACHE_KEY)
    if stats:
        return stats
    today = timezone.localdate()
    month_start = today.replace(day=1)
    week0 = today - timedelta(days=today.weekday() + 7 * 7)

    users = dict(ServiceUser.objects.values_list('status').annotate(n=Count('id')))
    staff = dict(StaffMember.objects.values_list('status').annotate(n=Count('id')))
    month_shifts = Shift.objects.filter(date__gte=month_start, date__lte=today)
    by_status = dict(month_shifts.values_list('status').annotate(n=Count('id')))
    done, missed = by_status.get('completed', 0), by_status.get('missed', 0)

    weekly = (Shift.objects.filter(date__gte=week0, date__lte=today, status='completed')
              .annotate(period=TruncWeek('date')).values('period').annotate(value=Sum('hours')))
    month_keys = []
    m = month_start
    for _ in range(6):
        month_keys.insert(0, m)
        m = (m - timedelta(days=1)).replace(day=1)
    enquiries = (Enquiry.objects.filter(created_at__date__gte=month_keys[0])
                 .annotate(period=TruncMonth('created_at')).values('period').annotate(value=Count('id')))
    by_service = (ServiceUser.objects.filter(status='active').values('service__title')
                  .annotate(n=Count('id')).order_by('-n'))
    status_labels = dict(Shift.STATUSES)

    stats = {
        'kpis': {
            'active_users': users.get('active', 0), 'pending_users': users.get('enquiry', 0),
            'active_staff': staff.get('active', 0), 'onboarding': staff.get('onboarding', 0),
            'shifts_today': Shift.objects.filter(date=today).exclude(status='cancelled').count(),
            'hours_month': float(month_shifts.filter(status='completed').aggregate(h=Sum('hours'))['h'] or 0),
            'completion': round(100 * done / (done + missed)) if done + missed else None,
            'new_enquiries': Enquiry.objects.filter(status='new').count(),
        },
        'charts': {
            'hours': _series(weekly, [week0 + timedelta(weeks=i) for i in range(8)], '%d %b'),
            'enquiries': _series(enquiries, month_keys, '%b'),
            'shifts': {'labels': [status_labels[k] for k, _ in Shift.STATUSES],
                       'keys': [k for k, _ in Shift.STATUSES],
                       'values': [by_status.get(k, 0) for k, _ in Shift.STATUSES]},
            'services': {'labels': [r['service__title'] or 'Not set' for r in by_service],
                         'values': [r['n'] for r in by_service]},
        },
    }
    cache.set(DASHBOARD_CACHE_KEY, stats, 60)
    return stats


class DashboardView(AccessMixin, TemplateView):
    template_name = 'careapp/dashboard.html'
    area = 'dashboard'

    def dispatch(self, request, *args, **kwargs):
        # People without the overview go straight to the first area they can use.
        user = request.user
        if user.is_authenticated and not can(user, 'dashboard'):
            for key, cfg in SECTIONS.items():
                if can(user, cfg['area']):
                    return redirect('careapp:section_list', key)
            for area, url in (('onboarding', 'careapp:onboarding'), ('users', 'careapp:users')):
                if can(user, area):
                    return redirect(url)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        stats = dashboard_stats()
        today = timezone.localdate()
        ctx.update(
            page_title='Dashboard', kpis=stats['kpis'], charts=stats['charts'], today=today,
            today_shifts=Shift.objects.filter(date=today).select_related('service_user', 'staff')
                                      .order_by('start_time')[:8],
            latest_enquiries=Enquiry.objects.order_by('-created_at')[:5],
            onboarding=StaffMember.objects.filter(status='onboarding').annotate(
                total=Count('onboarding_tasks'),
                done=Count('onboarding_tasks', filter=Q(onboarding_tasks__done=True)))[:4],
        )
        return ctx


# --------------------------------------------------------------------------
# Onboarding
# --------------------------------------------------------------------------
class OnboardingView(AccessMixin, TemplateView):
    template_name = 'careapp/onboarding.html'
    area = 'onboarding'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        people = StaffMember.objects.filter(status='onboarding').prefetch_related('onboarding_tasks')
        for p in people:
            tasks = list(p.onboarding_tasks.all())
            p.tasks, p.done_count = tasks, sum(t.done for t in tasks)
            p.percent = round(100 * p.done_count / len(tasks)) if tasks else 0
        ctx.update(page_title='Onboarding', people=people,
                   can_edit=can(self.request.user, 'onboarding', 'change'),
                   can_add_staff=can(self.request.user, 'staff', 'add'))
        return ctx

    def post(self, request, *args, **kwargs):
        if 'task' in request.POST:
            task = get_object_or_404(OnboardingTask, pk=request.POST['task'])
            task.done = not task.done
            task.done_at = timezone.now() if task.done else None
            task.save(update_fields=['done', 'done_at'])
        elif 'activate' in request.POST:
            person = get_object_or_404(StaffMember, pk=request.POST['activate'], status='onboarding')
            person.status = 'active'
            person.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'{person} is now an active team member.')
        cache.delete(DASHBOARD_CACHE_KEY)
        return redirect(f"{reverse('careapp:onboarding')}#staff-{request.POST.get('staff', '')}")


# --------------------------------------------------------------------------
# Private files (service user photos): permission-checked, never public
# --------------------------------------------------------------------------
PRIVATE_AREAS = {'service-users/': ('service_users', ServiceUser, 'photo')}


@login_required(login_url='careapp:login')
def private_media(request, name):
    match = next((v for prefix, v in PRIVATE_AREAS.items() if name.startswith(prefix)), None)
    if not match:
        raise Http404
    area, model, field = match
    if not can(request.user, area):
        raise PermissionDenied
    storage = model._meta.get_field(field).storage
    try:
        if not storage.exists(name):
            raise Http404
        response = FileResponse(storage.open(name, 'rb'))
    except SuspiciousFileOperation:
        raise Http404
    response['Cache-Control'] = 'private, max-age=3600'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
