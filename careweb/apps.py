from django.apps import AppConfig


class CarewebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'careweb'
    verbose_name = 'Care Anmore website'

    def ready(self):
        from . import security  # noqa: F401  (registers sign-in signal handlers)
