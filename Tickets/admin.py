from django.contrib import admin

from .models import Tickets


@admin.register(Tickets)
class TicketAdmin(admin.ModelAdmin):
    models = Tickets
    list_display = (
        "id",
        "email",
        "subject",
        "bodies",
        "status",
        "created_at",
        "updated_at"
    )
