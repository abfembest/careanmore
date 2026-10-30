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

## Team dashboard (`careapp`)

Go to http://127.0.0.1:8000/dashboard/ and sign in with a **staff** account
(`createsuperuser`, or tick "Staff status" for a user in `/admin/`).

| Menu | What it does |
| --- | --- |
| Dashboard | Service users, staff, shifts, care hours and enquiries at a glance, with charts |
| Care › Service users / Staff / Shifts | Search, filter, add, edit and delete records |
| Care › Onboarding | Checklist for each new starter (references, DBS, right to work, training…) |
| Website › Enquiries | Website enquiries with status and staff notes |
| Website › Site settings | General details, logos & branding, home page text, hero slides, services, FAQs, careers, footer |

Changes made under **Site settings** go live on the website immediately.

Preview the charts with sample data (every record is labelled "Demo"):

```
python manage.py seed_careapp_demo          # add
python manage.py seed_careapp_demo --clear  # remove
```

**Adding a dashboard section:** add one entry to `careapp/registry.py`
(model, fields, columns, search). List, add, edit and delete pages are generated.

**Uploaded logos and photos** are stored in `media/`. Django serves them only while
`DEBUG=True`; on a live server, configure your host (e.g. Nginx or your platform's
media storage) to serve `/media/`.

## Security and bot protection

All of this lives in `careweb/security.py` and needs no extra packages.

**Sign-in (dashboard and Django admin)**
* After 5 failed attempts for a username from one IP address, sign-in is paused for
  15 minutes, even with the right password. A single IP is paused after 20 failures
  across any usernames.
* Hidden honeypot field and a signed timer: forms sent in under 3 seconds are refused.
* Passwords need at least 10 characters. Sessions end after 8 hours.
* Failed and blocked attempts are written to the log (`careweb.security`).
* Optional: move Django admin to a private address with `DJANGO_ADMIN_URL`.

**Contact form**
* Honeypot and timer (bots are sent to the thank-you page, but nothing is saved).
* At most 5 enquiries per IP address per hour.
* Messages with more than 2 web links are refused.

**Optional CAPTCHA:** set `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY` (free
Cloudflare Turnstile) to add a privacy-friendly "are you human" check to both forms.

**Behind ngrok, Nginx or a hosting platform** set `DJANGO_TRUST_X_FORWARDED_FOR=True`,
otherwise every visitor looks like the same IP address and limits are shared.

**Running more than one server process?** Limits are kept in Django's cache. The
default memory cache is per process, so on a multi-process server use a shared
cache (Redis, or Django's database cache) via `CACHE_BACKEND` / `CACHE_LOCATION`.

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
