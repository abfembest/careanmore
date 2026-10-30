"""Bot protection and sign-in hardening shared by the website and the dashboard.

Layers (no third-party packages needed):
  * Honeypot field that people never see.
  * Signed time-trap: forms submitted too quickly (bots) or long after loading are rejected.
  * Per-IP rate limits (contact form) using the cache.
  * Sign-in lockout after repeated failures, for the dashboard AND Django admin.
  * Optional Cloudflare Turnstile challenge when TURNSTILE_* keys are set.
"""
import json
import logging
import time
import urllib.parse
import urllib.request

from django import forms
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core import signing
from django.core.cache import cache
from django.dispatch import receiver

logger = logging.getLogger('careweb.security')
SALT = 'careweb.form-timestamp'


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def client_ip(request):
    if request is None:
        return 'unknown'
    if getattr(settings, 'TRUST_X_FORWARDED_FOR', False):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[-1].strip()  # address added by our own proxy
    return request.META.get('REMOTE_ADDR', 'unknown')


def hit(key, window):
    """Increment a counter that expires `window` seconds after its first hit."""
    cache.add(key, 0, window)
    try:
        return cache.incr(key)
    except ValueError:  # expired between add and incr
        cache.set(key, 1, window)
        return 1


def rate_limited(request, scope, limit, window):
    """True once an IP has made more than `limit` attempts within `window` seconds."""
    count = hit(f'rl:{scope}:{client_ip(request)}', window)
    if count > limit:
        logger.warning('Rate limit hit for %s from %s', scope, client_ip(request))
        return True
    return False


def make_timestamp(offset=0):
    return signing.dumps(int(time.time()) + offset, salt=SALT)


def turnstile_ok(token, request):
    secret = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    if not secret:
        return True
    if not token:
        return False
    data = urllib.parse.urlencode({'secret': secret, 'response': token, 'remoteip': client_ip(request)}).encode()
    try:
        with urllib.request.urlopen('https://challenges.cloudflare.com/turnstile/v0/siteverify', data, timeout=5) as r:
            return bool(json.load(r).get('success'))
    except Exception:  # fail closed: no verification, no submission
        logger.exception('Turnstile verification failed')
        return False


# --------------------------------------------------------------------------
# Form mixin
# --------------------------------------------------------------------------
class BotProtectionMixin(forms.Form):
    """Adds a honeypot, a signed time-trap and (optionally) Turnstile to any form.

    After validation, `form.is_bot` is True for clear bot signals, so views can
    quietly discard the submission instead of telling the bot what went wrong.
    """
    website = forms.CharField(required=False, label='Leave this field empty',
                              widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))
    ts = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, request=None, **kwargs):
        self.is_bot = False
        super().__init__(*args, **kwargs)
        self.request = request  # set after super(): AuthenticationForm would reset it
        self.initial['ts'] = make_timestamp()
        self.fields['ts'].initial = self.initial['ts']

    def clean(self):
        data = super().clean()
        reason = self._bot_reason()
        if reason:
            self.is_bot = True
            logger.warning('Blocked bot submission (%s) on %s from %s',
                           reason, type(self).__name__, client_ip(self.request))
            raise forms.ValidationError('Something went wrong. Please wait a moment and try again.', code='bot')
        if not turnstile_ok(self.data.get('cf-turnstile-response'), self.request):
            raise forms.ValidationError('Please confirm you are not a robot and try again.', code='captcha')
        return data

    def _bot_reason(self):
        if self.data.get('website'):
            return 'honeypot'
        try:
            started = signing.loads(self.data.get('ts', ''), salt=SALT,
                                    max_age=getattr(settings, 'FORM_MAX_AGE_SECONDS', 6 * 3600))
        except signing.SignatureExpired:
            return ''  # page left open too long: a person, ask them to resend
        except signing.BadSignature:
            return 'missing or forged timestamp'
        if time.time() - started < getattr(settings, 'FORM_MIN_SECONDS', 3):
            return 'submitted too fast'
        return ''


# --------------------------------------------------------------------------
# Sign-in lockout (applies to every login: dashboard and Django admin)
# --------------------------------------------------------------------------
def _lock_keys(request, username):
    ip = client_ip(request)
    return f'login-fail:{ip}:{(username or "").lower()}', f'login-fail-ip:{ip}'


def login_locked(request, username):
    user_key, ip_key = _lock_keys(request, username)
    limit = getattr(settings, 'LOGIN_FAILURE_LIMIT', 5)
    return (cache.get(user_key, 0) >= limit) or (cache.get(ip_key, 0) >= limit * 4)


class LockoutModelBackend(ModelBackend):
    """Refuses to check passwords while an account/IP pair is locked out."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is not None and login_locked(request, username):
            logger.warning('Locked-out sign-in attempt for %r from %s', username, client_ip(request))
            return None
        return super().authenticate(request, username=username, password=password, **kwargs)


@receiver(user_login_failed)
def _record_failure(sender, credentials, request=None, **kwargs):
    if request is None:
        return
    window = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15) * 60
    for key in _lock_keys(request, credentials.get('username')):
        hit(key, window)
    logger.warning('Failed sign-in for %r from %s', credentials.get('username'), client_ip(request))


@receiver(user_logged_in)
def _clear_failures(sender, request, user, **kwargs):
    if request is not None:
        cache.delete(_lock_keys(request, user.get_username())[0])
