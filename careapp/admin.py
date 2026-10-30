from django.contrib import admin

from .models import OnboardingTask, ServiceUser, Shift, StaffMember


class OnboardingInline(admin.TabularInline):
    model = OnboardingTask
    extra = 0


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'role', 'status', 'start_date')
    list_filter = ('status', 'role')
    search_fields = ('first_name', 'last_name', 'email')
    inlines = [OnboardingInline]


@admin.register(ServiceUser)
class ServiceUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'service', 'weekly_hours')
    list_filter = ('status', 'service')
    search_fields = ('first_name', 'last_name', 'postcode')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'service_user', 'staff', 'hours', 'status')
    list_filter = ('status', 'date')
    list_select_related = ('service_user', 'staff')
    date_hierarchy = 'date'
