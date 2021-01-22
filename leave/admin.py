from django.contrib import admin
from leave.models import Leave, LeaveType, LeavePolicy


class PolicyInline(admin.TabularInline):
    model = LeavePolicy


class LeaveTypeAdmin(admin.ModelAdmin):
    inlines = [PolicyInline]
    list_display = ('name',)


class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_policy', 'start_date', 'end_date', 'leave_balance', 'relief', 'status')
    actions = ['approve_leave', 'decline_leave']

    def update_status(self, request, queryset, status):
        rows_updated = queryset.update(status=status)
        self.message_user(request, 'Leave request(s) successfully updated')

    def approve_leave(self, request, queryset):
        self.update_status(request, queryset, Leave.APPROVED)

    approve_leave.short_description = 'Approve Leave'

    def decline_leave(self, request, queryset):
        self.update_status(request, queryset, Leave.REJECTED)

    decline_leave.short_description = 'Decline Leave'


admin.site.register(LeaveType, LeaveTypeAdmin)
admin.site.register(Leave, LeaveAdmin)

