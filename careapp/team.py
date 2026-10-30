"""Users & roles: who can sign in, and what each role may do (the permission matrix)."""
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from .models import Role, RoleAssignment
from .permissions import ACTIONS, AREAS, can
from .views import AccessMixin

User = get_user_model()


class UserForm(forms.ModelForm):
    role = forms.ModelChoiceField(Role.objects.all(), empty_label='No dashboard access')
    password1 = forms.CharField(label='Password', required=False, strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label='Confirm password', required=False, strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {'is_active': 'Account active (can sign in)'}

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.fields['role'].required = False
        assignment = getattr(self.instance, 'dashboard_role', None) if self.instance.pk else None
        self.fields['role'].initial = assignment.role_id if assignment else None
        if self.instance.pk:
            self.fields['password1'].help_text = 'Leave blank to keep the current password.'
        else:
            self.fields['password1'].required = self.fields['password2'].required = True
        if self.instance.is_superuser:
            self.fields['role'].help_text = 'Superusers always have full access.'

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1'), data.get('password2')
        if p1 or p2:
            if p1 != p2:
                self.add_error('password2', 'The two passwords do not match.')
            else:
                try:
                    validate_password(p1, self.instance)
                except forms.ValidationError as e:
                    self.add_error('password1', e)
        if self.instance.pk == self.editor.pk:
            if not data.get('is_active'):
                self.add_error('is_active', 'You cannot deactivate your own account.')
            if not self.editor.is_superuser and data.get('role') != getattr(
                    getattr(self.instance, 'dashboard_role', None), 'role', None):
                self.add_error('role', 'Ask another administrator to change your own role.')
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        user.save()
        role = self.cleaned_data.get('role')
        if role:
            RoleAssignment.objects.update_or_create(user=user, defaults={'role': role})
        else:
            RoleAssignment.objects.filter(user=user).delete()
        return user


class UserListView(AccessMixin, ListView):
    template_name = 'careapp/users.html'
    area, write_action = 'users', 'view'

    def get_queryset(self):
        return User.objects.select_related('dashboard_role__role').order_by('-is_active', 'username')

    def get_context_data(self, **kwargs):
        return super().get_context_data(page_title='Users', can_add=can(self.request.user, 'users', 'add'), **kwargs)


class UserFormView(AccessMixin, TemplateView):
    template_name = 'careapp/user_form.html'
    area = 'users'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(User, pk=kwargs['pk']) if 'pk' in kwargs else User()
        if not self.object.pk:
            self.action = self.write_action = 'add'
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        # Only superusers may change superuser accounts.
        if self.object.is_superuser and not self.request.user.is_superuser:
            return self.request.method == 'GET' and super().test_func()
        return super().test_func()

    def get_form(self):
        form = UserForm(self.request.POST or None, instance=self.object, editor=self.request.user)
        if not can(self.request.user, 'users', 'change' if self.object.pk else 'add') or (
                self.object.is_superuser and not self.request.user.is_superuser):
            for f in form.fields.values():
                f.disabled = True
        return form

    def get_context_data(self, form=None, **kwargs):
        title = f'{self.object.get_full_name() or self.object.username}' if self.object.pk else 'New user'
        return super().get_context_data(page_title=title, form=form or self.get_form(), object=self.object, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Saved user “{user.username}”.')
            return redirect('careapp:users')
        return self.render_to_response(self.get_context_data(form=form))


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description']


class RoleMatrixView(AccessMixin, TemplateView):
    """All roles side by side: rows are area × action, columns are roles."""
    template_name = 'careapp/roles.html'
    area, write_action = 'users', 'view'  # each POST branch checks its own action

    def get_context_data(self, **kwargs):
        roles = list(Role.objects.annotate(users=Count('assignments')))
        rows = []
        for area, (label, actions) in AREAS.items():
            for i, (action, action_label) in enumerate(ACTIONS):
                if action not in actions:
                    continue
                rows.append({'area': area, 'area_label': label, 'first': not any(r['area'] == area for r in rows),
                             'span': len(actions), 'action': action, 'action_label': action_label,
                             'cells': [(role, role.allows(area, action)) for role in roles]})
        return super().get_context_data(page_title='Roles & permissions', roles=roles, rows=rows,
                                        new_form=kwargs.get('new_form') or RoleForm(),
                                        can_edit=can(self.request.user, 'users', 'change'),
                                        can_add=can(self.request.user, 'users', 'add'), **kwargs)

    def post(self, request, *args, **kwargs):
        if 'create' in request.POST:
            if not can(request.user, 'users', 'add'):
                return self.handle_no_permission()
            form = RoleForm(request.POST)
            if not form.is_valid():
                return self.render_to_response(self.get_context_data(new_form=form))
            role = form.save()
            messages.success(request, f'Created role “{role}”. Tick its permissions below and save.')
            return redirect('careapp:roles')
        if 'delete' in request.POST:
            if not can(request.user, 'users', 'delete'):
                return self.handle_no_permission()
            role = get_object_or_404(Role, pk=request.POST['delete'], is_locked=False)
            if role.assignments.exists():
                messages.error(request, f'“{role}” is still assigned to people. Give them another role first.')
            else:
                role.delete()
                messages.success(request, f'Deleted role “{role}”.')
            return redirect('careapp:roles')
        if not can(request.user, 'users', 'change'):
            return self.handle_no_permission()
        # Save the whole matrix in one go.
        checked = set(request.POST.getlist('perm'))
        for role in Role.objects.filter(is_locked=False):
            role.permissions = {
                area: [a for a in actions if f'{role.pk}:{area}:{a}' in checked]
                for area, (_, actions) in AREAS.items()
            }
            role.save(update_fields=['permissions', 'updated_at'])
        messages.success(request, 'Permissions saved. They apply the next time each person loads a page.')
        return redirect('careapp:roles')
