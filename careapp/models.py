"""Care operations data: staff, service users, shifts and staff onboarding."""
from datetime import datetime
from decimal import Decimal

from django.db import models
from django.utils import timezone

from careweb.models import Service, TimeStampedModel

ONBOARDING_STEPS = [
    'Application and interview',
    'Two references received',
    'Enhanced DBS check',
    'Right to work check',
    'Care Certificate training',
    'Induction completed',
    'Shadow shifts completed',
]


class StaffMember(TimeStampedModel):
    ROLES = [('carer', 'Care worker'), ('senior', 'Senior carer'), ('coordinator', 'Care coordinator'),
             ('manager', 'Manager'), ('office', 'Office team')]
    STATUSES = [('onboarding', 'Onboarding'), ('active', 'Active'), ('leave', 'On leave'), ('left', 'Left')]

    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    role = models.CharField(max_length=20, choices=ROLES, default='carer')
    status = models.CharField(max_length=20, choices=STATUSES, default='onboarding', db_index=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'staff member'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.status == 'onboarding':
            OnboardingTask.objects.bulk_create(
                OnboardingTask(staff=self, title=t, order=i) for i, t in enumerate(ONBOARDING_STEPS)
            )


class OnboardingTask(models.Model):
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='onboarding_tasks')
    title = models.CharField(max_length=120)
    order = models.PositiveSmallIntegerField(default=0)
    done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class ServiceUser(TimeStampedModel):
    STATUSES = [('enquiry', 'Assessment pending'), ('active', 'Receiving care'),
                ('paused', 'Paused'), ('ended', 'Care ended')]

    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    status = models.CharField(max_length=20, choices=STATUSES, default='enquiry', db_index=True)
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL,
                                verbose_name='main service')
    postcode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    weekly_hours = models.DecimalField('planned hours a week', max_digits=5, decimal_places=1, default=0)
    start_date = models.DateField(null=True, blank=True)
    key_contact = models.CharField('family or representative', max_length=120, blank=True)
    notes = models.TextField(blank=True, help_text='Avoid detailed medical information here.')

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'service user'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Shift(TimeStampedModel):
    STATUSES = [('scheduled', 'Scheduled'), ('completed', 'Completed'),
                ('missed', 'Missed'), ('cancelled', 'Cancelled')]

    service_user = models.ForeignKey(ServiceUser, on_delete=models.CASCADE, related_name='shifts')
    staff = models.ForeignKey(StaffMember, null=True, blank=True, on_delete=models.SET_NULL, related_name='shifts')
    date = models.DateField(default=timezone.localdate, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    hours = models.DecimalField(max_digits=4, decimal_places=2, default=0, editable=False)
    status = models.CharField(max_length=20, choices=STATUSES, default='scheduled', db_index=True)
    notes = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ['-date', 'start_time']
        indexes = [models.Index(fields=['date', 'status'])]

    def __str__(self):
        return f'{self.service_user} · {self.date:%d %b} {self.start_time:%H:%M}'

    def save(self, *args, **kwargs):
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        minutes = (end - start).total_seconds() / 60
        if minutes < 0:  # overnight shift
            minutes += 24 * 60
        self.hours = Decimal(minutes / 60).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)
