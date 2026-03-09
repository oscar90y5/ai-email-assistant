from django.contrib import admin
from .models import Email


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ["subject", "sender", "classification", "notified", "received_at"]
    list_filter = ["classification", "notified"]
    search_fields = ["subject", "sender", "gmail_id"]
    readonly_fields = ["gmail_id", "created_at", "received_at"]
