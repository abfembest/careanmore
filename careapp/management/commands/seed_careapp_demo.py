"""Fill the dashboard with clearly-labelled DEMO data so the charts can be previewed.

    python manage.py seed_careapp_demo          # add demo data
    python manage.py seed_careapp_demo --clear  # remove all demo data again
"""
import random
from datetime import time, timedelta

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from careweb.models import Enquiry, Service

from careapp.models import ServiceUser, Shift, StaffMember

TAG = '[DEMO]'
FIRST = ['Alex', 'Sam', 'Jordan', 'Morgan', 'Taylor', 'Casey', 'Riley', 'Jamie', 'Robin', 'Avery', 'Quinn', 'Rowan']
LAST = ['Demo-Ash', 'Demo-Birch', 'Demo-Cedar', 'Demo-Elm', 'Demo-Hazel', 'Demo-Oak', 'Demo-Rowan', 'Demo-Yew']


class Command(BaseCommand):
    help = 'Add or remove demo staff, service users and shifts for previewing the dashboard.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Remove demo data instead.')

    def handle(self, *args, clear=False, **opts):
        ServiceUser.objects.filter(notes=TAG).delete()
        StaffMember.objects.filter(notes=TAG).delete()
        Enquiry.objects.filter(message=TAG).delete()
        cache.delete('careapp:dashboard-stats')
        if clear:
            return self.stdout.write(self.style.SUCCESS('Demo data removed.'))

        rnd = random.Random(7)
        services = list(Service.objects.all()) or [None]
        name = lambda: (rnd.choice(FIRST), rnd.choice(LAST))  # noqa: E731
        staff = [StaffMember.objects.create(first_name=f, last_name=l, notes=TAG, status=st, role=rnd.choice(['carer', 'carer', 'senior']))
                 for (f, l), st in ((name(), 'active') for _ in range(9))]
        for _ in range(3):
            f, l = name()
            s = StaffMember.objects.create(first_name=f, last_name=l, notes=TAG, status='onboarding')
            s.onboarding_tasks.filter(order__lt=rnd.randint(1, 6)).update(done=True, done_at=timezone.now())
        users = [ServiceUser.objects.create(first_name=f, last_name=l, notes=TAG, status=st,
                                            service=rnd.choice(services), weekly_hours=rnd.choice([3.5, 7, 10.5, 14]))
                 for (f, l), st in ((name(), rnd.choice(['active'] * 5 + ['enquiry', 'paused'])) for _ in range(18))]
        active = [u for u in users if u.status == 'active']

        today = timezone.localdate()
        shifts = []
        for day in range(-56, 7):
            date = today + timedelta(days=day)
            for _ in range(rnd.randint(6, 12)):
                start = time(rnd.choice([7, 8, 9, 12, 13, 17, 19]), rnd.choice([0, 30]))
                end = time(start.hour + rnd.choice([1, 1, 2]), start.minute)
                status = 'scheduled' if day > 0 else rnd.choices(
                    ['completed', 'missed', 'cancelled'], [92, 3, 5])[0] if day < 0 else rnd.choice(['completed', 'scheduled'])
                shifts.append(Shift(service_user=rnd.choice(active), staff=rnd.choice(staff), date=date,
                                    start_time=start, end_time=end, status=status, notes=TAG))
        for s in shifts:  # compute hours without a save() per row
            s.hours = (s.end_time.hour * 60 + s.end_time.minute - s.start_time.hour * 60 - s.start_time.minute) / 60
        Shift.objects.bulk_create(shifts, batch_size=500)
        topics = [t for t, _ in Enquiry.TOPICS]
        for i in range(24):
            e = Enquiry.objects.create(name=f'{rnd.choice(FIRST)} {rnd.choice(LAST)}', contact_method='email',
                                       email='demo@example.com', topic=rnd.choice(topics), message=TAG, consent=True,
                                       status='new' if i < 3 else rnd.choice(['contacted', 'closed']))
            Enquiry.objects.filter(pk=e.pk).update(created_at=timezone.now() - timedelta(days=rnd.randint(0, 170)))
        self.stdout.write(self.style.SUCCESS(f'Added demo data: {len(staff) + 3} staff, {len(users)} service users, {len(shifts)} shifts, 24 enquiries.'))
