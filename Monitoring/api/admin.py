# api/admin.py
from django.contrib import admin, messages
from django.utils import timezone
from django.db.models import Count

from .models import Service, Endpoint, CheckResult


# ---------- Inline for Endpoints on the Service page ----------
class EndpointInline(admin.TabularInline):
    model = Endpoint
    extra = 0
    fields = (
        "url", "method", "expected_status",
        "timeout_ms", "interval_sec",
        "enabled", "next_run_at",
    )
    readonly_fields = ("next_run_at",)
    show_change_link = True


# ---------- Actions for Endpoints ----------
@admin.action(description="Enable selected endpoints")
def enable_endpoints(modeladmin, request, queryset):
    updated = queryset.update(enabled=True)
    messages.success(request, f"Enabled {updated} endpoint(s).")


@admin.action(description="Disable selected endpoints")
def disable_endpoints(modeladmin, request, queryset):
    updated = queryset.update(enabled=False)
    messages.success(request, f"Disabled {updated} endpoint(s).")


@admin.action(description="Schedule run now (set next_run_at = now)")
def schedule_run_now(modeladmin, request, queryset):
    updated = queryset.update(next_run_at=timezone.now())
    messages.info(request, f"Scheduled {updated} endpoint(s) to run now.")


# ---------- Endpoint Admin ----------
@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = (
        "id", "service", "short_url", "method",
        "expected_status", "enabled",
        "interval_sec", "timeout_ms", "next_run_at",
    )
    list_filter = ("enabled", "method", "expected_status", "service")
    search_fields = ("url", "service__name")
    autocomplete_fields = ("service",)
    actions = [enable_endpoints, disable_endpoints, schedule_run_now]
    readonly_fields = ()
    ordering = ("service__name", "id")

    def short_url(self, obj):
        return (obj.url[:80] + "…") if len(obj.url) > 80 else obj.url
    short_url.short_description = "URL"


# ---------- Service Admin ----------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "status", "last_checked", "endpoints_count")
    list_filter = ("status",)
    search_fields = ("name", "url")
    inlines = [EndpointInline]
    readonly_fields = ("status", "last_checked")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_ep_count=Count("endpoint")) 

    def endpoints_count(self, obj):
        return getattr(obj, "_ep_count", 0)
    endpoints_count.short_description = "Endpoints"

    @admin.action(description="Recompute service status from last 10 results")
    def recompute_status(self, request, queryset):
        for svc in queryset:
            last10 = list(
                CheckResult.objects.filter(endpoint__service=svc.id).order_by("-timestamp")[:10]
            )
            svc.status = "UNHEALTHY" if any(not c.success for c in last10) else "HEALTHY"
            svc.last_checked = timezone.now()
            svc.save(update_fields=["status", "last_checked"])
        messages.success(request, f"Recomputed status for {queryset.count()} service(s).")

    actions = ["recompute_status"]


# ---------- CheckResult Admin ----------
@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = (
        "id", "service_name", "endpoint_id", "timestamp",
        "status_code", "response_time_ms", "success", "short_details",
    )
    list_filter = ("success", "status_code", "endpoint__method", "endpoint__service")
    search_fields = ("endpoint__url", "endpoint__service__name", "details")
    readonly_fields = ("endpoint", "timestamp", "status_code", "response_time_ms", "success", "details")
    ordering = ("-timestamp",)

    def service_name(self, obj):
        return obj.endpoint.service.name

    def short_details(self, obj):
        if not obj.details:
            return ""
        return (obj.details[:80] + "…") if len(obj.details) > 80 else obj.details
    short_details.short_description = "Details"
