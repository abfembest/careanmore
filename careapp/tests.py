from datetime import time

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from careweb.models import HomePage, Service, SiteSettings

from django.core.cache import cache

from careweb.security import make_timestamp

from .models import Role, RoleAssignment, ServiceUser, Shift, StaffMember
from .registry import SECTIONS, SETTINGS_PAGES


class DashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('manager', password='pass-12345')
        RoleAssignment.objects.create(user=self.user, role=Role.objects.get(name='Administrator'))
        self.client.force_login(self.user)

    def test_requires_staff_login(self):
        self.client.logout()
        r = self.client.get(reverse('careapp:dashboard'))
        self.assertRedirects(r, reverse('careapp:login') + '?next=/dashboard/')
        get_user_model().objects.create_user('visitor', password='pass-12345')
        self.client.login(username='visitor', password='pass-12345')
        self.assertEqual(self.client.get(reverse('careapp:dashboard')).status_code, 403)

    def test_every_page_loads(self):
        urls = [reverse('careapp:dashboard'), reverse('careapp:onboarding')]
        urls += [reverse('careapp:section_list', args=[k]) for k in SECTIONS]
        urls += [reverse('careapp:section_create', args=[k]) for k, c in SECTIONS.items() if c.get('can_create', True)]
        urls += [reverse('careapp:settings', args=[k]) for k in SETTINGS_PAGES]
        urls += [reverse('careapp:users'), reverse('careapp:user_create'), reverse('careapp:roles'),
                 reverse('careapp:user_edit', args=[self.user.pk])]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_stats(self):
        u = ServiceUser.objects.create(first_name='A', last_name='B', status='active')
        Shift.objects.create(service_user=u, start_time=time(9), end_time=time(11, 30), status='completed')
        r = self.client.get(reverse('careapp:dashboard'))
        self.assertEqual(r.context['kpis']['active_users'], 1)
        self.assertEqual(r.context['kpis']['hours_month'], 2.5)
        self.assertContains(r, 'chart-data')

    def test_crud_and_search(self):
        r = self.client.post(reverse('careapp:section_create', args=['staff']), {
            'first_name': 'Jo', 'last_name': 'Bloggs', 'role': 'carer', 'status': 'onboarding', 'start_date': '2026-10-01'})
        self.assertRedirects(r, reverse('careapp:section_list', args=['staff']))
        jo = StaffMember.objects.get(first_name='Jo')
        self.assertEqual(jo.onboarding_tasks.count(), 7)
        self.assertContains(self.client.get(reverse('careapp:section_list', args=['staff']) + '?q=blogg'), 'Jo Bloggs')
        self.client.post(reverse('careapp:section_delete', args=['staff', jo.pk]))
        self.assertFalse(StaffMember.objects.exists())

    def test_onboarding_toggle_and_activate(self):
        jo = StaffMember.objects.create(first_name='Jo', last_name='B')
        for t in jo.onboarding_tasks.all():
            self.client.post(reverse('careapp:onboarding'), {'task': t.pk, 'staff': jo.pk})
        self.assertFalse(jo.onboarding_tasks.filter(done=False).exists())
        self.client.post(reverse('careapp:onboarding'), {'activate': jo.pk})
        jo.refresh_from_db()
        self.assertEqual(jo.status, 'active')

    def test_site_settings_update_live_site(self):
        data = {f: getattr(SiteSettings.load(), f) for f in SETTINGS_PAGES['footer']['fields']}
        data['footer_text'] = 'Brand new footer words'
        data['show_help_strip'] = ''
        self.client.post(reverse('careapp:settings', args=['footer']), data)
        r = self.client.get(reverse('careweb:home'))
        self.assertContains(r, 'Brand new footer words')
        self.assertNotContains(r, 'Need help now?')

    def test_home_page_text_is_editable(self):
        page = HomePage.load()
        page.services_title = 'Care for every day'
        page.save()
        self.assertContains(self.client.get(reverse('careweb:home')), 'Care for every day')

    @override_settings(MEDIA_ROOT='/tmp/careapp-test-media')
    def test_logo_upload(self):
        svg = SimpleUploadedFile('logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg"/>', 'image/svg+xml')
        self.client.post(reverse('careapp:settings', args=['branding']), {'logo': svg})
        self.assertIn('/media/branding/logo', self.client.get(reverse('careweb:home')).content.decode())

    def test_service_edit_reflects_on_site(self):
        svc = Service.objects.get(slug='personal-care')
        url = reverse('careapp:section_edit', args=['services', svc.pk])
        form = self.client.get(url).context['form']
        data = {k: v for k, v in form.initial.items() if v is not None and k != 'image'}
        data.update(title='Personal care at home', is_featured='on', is_published='on')
        self.client.post(url, data)
        self.assertContains(self.client.get(reverse('careweb:home')), 'Personal care at home')


class LoginSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        get_user_model().objects.create_superuser('manager', 'm@example.com', 'correct-horse-1')
        self.url = reverse('careapp:login')

    def post(self, password, **extra):
        data = {'username': 'manager', 'password': password, 'ts': make_timestamp(offset=-10), 'website': ''}
        data.update(extra)
        return self.client.post(self.url, data)

    def test_login_page_shows_brand(self):
        self.assertContains(self.client.get(self.url), 'For the Care Anmore Ltd team only')

    def test_valid_login(self):
        self.assertRedirects(self.post('correct-horse-1'), reverse('careapp:dashboard'))

    def test_lockout_after_repeated_failures(self):
        for _ in range(5):
            self.post('wrong')
        r = self.post('correct-horse-1')  # right password is refused while locked
        self.assertContains(r, 'sign-in is paused')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_lockout_also_protects_django_admin(self):
        for _ in range(5):
            self.post('wrong')
        self.client.post(reverse('admin:login'), {'username': 'manager', 'password': 'correct-horse-1'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_bot_login_blocked(self):
        self.assertNotIn('_auth_user_id', self.client.session)
        self.post('correct-horse-1', website='http://spam')
        self.post('correct-horse-1', ts=make_timestamp())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_success_resets_counter(self):
        for _ in range(4):
            self.post('wrong')
        self.assertRedirects(self.post('correct-horse-1'), reverse('careapp:dashboard'))


class PermissionMatrixTests(TestCase):
    def make_user(self, name, role_name):
        user = get_user_model().objects.create_user(name, password='a-long-password-1')
        RoleAssignment.objects.create(user=user, role=Role.objects.get(name=role_name))
        return user

    def test_default_roles_created(self):
        self.assertEqual(Role.objects.count(), 5)
        self.assertTrue(Role.objects.get(name='Administrator').is_locked)

    def test_care_worker_is_read_only_and_limited(self):
        self.client.force_login(self.make_user('carer', 'Care worker'))
        # no overview: sent to the first area they can use
        self.assertRedirects(self.client.get(reverse('careapp:dashboard')), reverse('careapp:section_list', args=['service-users']))
        r = self.client.get(reverse('careapp:section_list', args=['shifts']))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Add shift')
        self.assertNotContains(r, 'Site settings')
        self.assertNotContains(r, 'Enquiries')
        for url in [reverse('careapp:section_create', args=['shifts']), reverse('careapp:section_list', args=['enquiries']),
                    reverse('careapp:settings', args=['general']), reverse('careapp:roles')]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        u = ServiceUser.objects.create(first_name='Ann', last_name='Lee')
        url = reverse('careapp:section_edit', args=['service-users', u.pk])
        self.assertContains(self.client.get(url), 'does not allow changes')
        self.assertEqual(self.client.post(url, {'first_name': 'X', 'last_name': 'Y', 'status': 'active'}).status_code, 403)

    def test_office_admin_edits_site_not_care(self):
        self.client.force_login(self.make_user('office', 'Office administrator'))
        self.assertEqual(self.client.get(reverse('careapp:settings', args=['footer'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('careapp:section_list', args=['service-users'])).status_code, 403)

    def test_matrix_save_changes_access(self):
        admin = get_user_model().objects.create_superuser('boss', 'b@example.com', 'a-long-password-1')
        carer_role = Role.objects.get(name='Care worker')
        self.client.force_login(admin)
        self.client.post(reverse('careapp:roles'), {'perm': [f'{carer_role.pk}:shifts:view', f'{carer_role.pk}:shifts:add']})
        carer_role.refresh_from_db()
        self.assertEqual(carer_role.permissions['shifts'], ['view', 'add'])
        self.assertEqual(carer_role.permissions['service_users'], [])
        # locked Administrator role is untouched
        self.assertTrue(Role.objects.get(name='Administrator').allows('users', 'delete'))

    def test_create_user_with_role(self):
        self.client.force_login(get_user_model().objects.create_superuser('boss', 'b@example.com', 'a-long-password-1'))
        role = Role.objects.get(name='Care coordinator')
        r = self.client.post(reverse('careapp:user_create'), {
            'username': 'jo', 'first_name': 'Jo', 'last_name': 'B', 'email': 'jo@example.com', 'is_active': 'on',
            'role': role.pk, 'password1': 'Purple-Tiger-77', 'password2': 'Purple-Tiger-77'})
        self.assertRedirects(r, reverse('careapp:users'))
        jo = get_user_model().objects.get(username='jo')
        self.assertEqual(jo.dashboard_role.role, role)
        self.assertTrue(jo.check_password('Purple-Tiger-77'))

    def test_cannot_change_own_role(self):
        mgr = self.make_user('mgr', 'Registered manager')
        role = Role.objects.get(name='Registered manager')
        role.permissions['users'] = ['view', 'change']
        role.save()
        self.client.force_login(mgr)
        r = self.client.post(reverse('careapp:user_edit', args=[mgr.pk]), {
            'username': 'mgr', 'is_active': 'on', 'role': Role.objects.get(name='Administrator').pk})
        self.assertContains(r, 'Ask another administrator')
        mgr.refresh_from_db()
        self.assertEqual(mgr.dashboard_role.role.name, 'Registered manager')

    def test_service_user_photo_is_private(self):
        boss = get_user_model().objects.create_superuser('boss', 'b@example.com', 'a-long-password-1')
        u = ServiceUser.objects.create(first_name='Ann', last_name='Lee')
        u.photo.save('ann.png', SimpleUploadedFile('ann.png', b'\x89PNG fake'))
        self.assertTrue(u.photo_url.startswith('/dashboard/private-media/service-users/'))
        self.assertEqual(self.client.get(u.photo_url).status_code, 302)  # signed out -> sign-in page
        self.client.force_login(self.make_user('office', 'Office administrator'))
        self.assertEqual(self.client.get(u.photo_url).status_code, 403)  # role can't see service users
        self.client.force_login(boss)
        r = self.client.get(u.photo_url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(self.client.get(reverse('careapp:section_list', args=['service-users'])), 'avatar-img')
        self.assertEqual(self.client.get(reverse('careapp:private_media', args=['service-users/../../settings.py'])).status_code, 404)
        u.photo.delete()

    def test_home_page_has_sign_in_link(self):
        r = self.client.get(reverse('careweb:home'))
        self.assertContains(r, reverse('careapp:login'))
        self.assertContains(r, 'Staff sign in')
        self.assertContains(r, 'href="https://careanmore.co.uk/webmail"')
