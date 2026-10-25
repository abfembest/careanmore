import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import FAQ, Enquiry, HeroSlide, Service, SiteSettings, Vacancy


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Organisation', {'fields': ('organisation_name', 'tagline', 'company_number')}),
        ('Contact details', {'fields': ('phone', 'email', 'address', 'service_area', 'opening_hours')}),
        ('Regulation', {'fields': ('cqc_location_id',)}),
        ('Social links', {'fields': ('facebook_url', 'linkedin_url', 'instagram_url'), 'classes': ('collapse',)}),
        ('Launch', {'fields': ('show_preview_banner',)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class ImagePreviewMixin:
    @admin.display(description='Image')
    def preview(self, obj):
        return format_html('<img src="{}" alt="" style="height:48px;width:72px;object-fit:cover;border-radius:6px">', obj.image_src)


@admin.register(HeroSlide)
class HeroSlideAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ('preview', 'heading', 'order', 'is_published')
    list_display_links = ('preview', 'heading')
    list_editable = ('order', 'is_published')


@admin.register(Service)
class ServiceAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ('preview', 'title', 'icon', 'order', 'is_featured', 'is_published')
    list_display_links = ('preview', 'title')
    list_editable = ('order', 'is_featured', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'summary', 'body')
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'icon', 'summary')}),
        ('Page content', {'fields': ('intro', 'body', 'includes')}),
        ('Image', {'fields': ('image', 'image_url', 'image_alt')}),
        ('Display', {'fields': ('order', 'is_featured', 'is_published', 'meta_description')}),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'show_on_home', 'is_published')
    list_editable = ('order', 'show_on_home', 'is_published')
    list_filter = ('category', 'is_published')
    search_fields = ('question', 'answer')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'contract', 'closing_date', 'is_published')
    list_filter = ('contract', 'is_published')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'contact_method', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'topic', 'contact_method', 'created_at')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'phone', 'postcode', 'message')
    readonly_fields = ('created_at', 'updated_at', 'source_page', 'consent')
    date_hierarchy = 'created_at'
    actions = ['mark_contacted', 'export_csv']
    fieldsets = (
        ('Contact', {'fields': ('name', 'contact_method', 'email', 'phone', 'postcode')}),
        ('Enquiry', {'fields': ('topic', 'service', 'message', 'consent', 'source_page')}),
        ('Follow-up', {'fields': ('status', 'staff_notes', 'created_at', 'updated_at')}),
    )

    @admin.action(description='Mark selected as contacted')
    def mark_contacted(self, request, queryset):
        queryset.update(status='contacted')

    @admin.action(description='Export selected to CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="enquiries.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Name', 'Topic', 'Contact method', 'Email', 'Phone', 'Postcode', 'Service', 'Status', 'Message'])
        for e in queryset:
            writer.writerow([
                e.created_at.strftime('%d/%m/%Y %H:%M'), e.name, e.get_topic_display(),
                e.get_contact_method_display(), e.email, e.phone, e.postcode,
                e.service or '', e.get_status_display(), e.message,
            ])
        return response
