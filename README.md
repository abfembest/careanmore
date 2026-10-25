# Care Anmore website

Django website for Care Anmore Ltd. The project config is `careanmor/`, and every
public page, template, stylesheet, script and image lives in the **`careweb`** app.

## Run it locally (Windows)

```powershell
cd C:\careanmore
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate          # creates tables and loads starter content
python manage.py createsuperuser  # for the admin
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the site and http://127.0.0.1:8000/admin/ to edit content.

## Pages

| URL | Page |
| --- | --- |
| `/` | Home: hero carousel, services, approach, steps, area, FAQs |
| `/about/` | About us, values, "we will / we won't" |
| `/our-care/` and `/our-care/<slug>/` | Service list and service pages |
| `/how-it-works/` | Getting started |
| `/faqs/` | Grouped FAQs |
| `/careers/` and `/careers/<slug>/` | Vacancies (shows "register your interest" when empty) |
| `/contact/` | Enquiry form (saved to the database, emailed to the team) |
| `/privacy/`, `/cookies/`, `/accessibility/` | Draft statements to review |
| `/sitemap.xml`, `/robots.txt` | SEO |

## Editing content (admin)

* **Site settings**: phone, email, address, opening hours, company number, CQC
  location ID (adds a CQC profile link), social links, and the **preview banner**
  (turn it off at launch).
* **Hero slides**: carousel slides, order, buttons and images.
* **Services**: title, icon, summary, page text, "what support can include" list, image.
* **FAQs**, **Vacancies**.
* **Enquiries**: status tracking, staff notes, CSV export.

Images: upload a photo, or paste an image URL. Starter photos are free Unsplash
images (https://unsplash.com/license) loaded from Unsplash; replace them with your
own photography when you can. If a photo can't load, a branded illustration shows instead.

**Logo:** `careweb/static/careweb/img/logo.svg` is a placeholder. To use your own,
save it as `careweb/static/careweb/img/care-anmore-logo.png` and change `logo.svg`
to `care-anmore-logo.png` in `templates/careweb/partials/header.html` and `footer.html`.

Reload starter content any time: `python manage.py seed_careweb` (add `--reset` to replace it).

## Going live

1. Copy `.env.example` to `.env` and set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`,
   `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.
2. Set the email settings and `ENQUIRY_NOTIFY_EMAILS` so enquiries reach the team.
3. Optional: switch to PostgreSQL with the `DATABASE_*` variables.
4. `python manage.py collectstatic` (WhiteNoise serves static files).
5. `python manage.py check --deploy`
6. Review the privacy, cookies and accessibility drafts and all service wording,
   add verified contact details, then turn off the preview banner.

## Tests

```
python manage.py test careweb
```
