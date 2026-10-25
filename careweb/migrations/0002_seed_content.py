from django.db import migrations


def load_content(apps, schema_editor):
    from careweb.content import seed

    seed(
        apps.get_model('careweb', 'SiteSettings'),
        apps.get_model('careweb', 'HeroSlide'),
        apps.get_model('careweb', 'Service'),
        apps.get_model('careweb', 'FAQ'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('careweb', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_content, migrations.RunPython.noop),
    ]
