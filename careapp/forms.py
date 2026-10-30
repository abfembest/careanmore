from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

from careweb.security import BotProtectionMixin, login_locked


class SecureLoginForm(BotProtectionMixin, AuthenticationForm):
    """Sign-in form with lockout, honeypot, time-trap and optional Turnstile."""

    def __init__(self, request=None, *args, **kwargs):  # AuthenticationForm takes request first
        super().__init__(*args, request=request, **kwargs)

    def clean(self):
        if login_locked(self.request, self.data.get('username')):
            raise forms.ValidationError(
                f'Too many failed attempts. For your security, sign-in is paused for '
                f'{settings.LOGIN_LOCKOUT_MINUTES} minutes.', code='locked')
        return super().clean()
