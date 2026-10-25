"""Root URL configuration for the Care Anmore project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from careweb.sitemaps import sitemaps
from careweb.views import robots_txt

admin.site.site_header = 'Care Anmore administration'
admin.site.site_title = 'Care Anmore admin'
admin.site.index_title = 'Website content and enquiries'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('', include('careweb.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'careweb.views.error_404'
handler500 = 'careweb.views.error_500'
