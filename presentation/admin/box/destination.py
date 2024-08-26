from django.contrib import admin
from infrastructure.box.models import Destination
from presentation.admin.box.inline import AssignInline, ConditionRuleInline


class AssignReplyInline(AssignInline):
    fk_name = "destination"


class ConditionRuleDestinationInline(ConditionRuleInline):
    fk_name = "destination"


@ admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = (
        "destination_type",
        "piece",
        "behavior",
        "reply",
        "written",
        "message_link",
        "url",
        "is_default",
        "order",
        "deleted"
    )
    search_fields = (
        "piece__name",
        "behavior__name",
        "reply__title",
        "written__extra__name",
        "message_link__message",
        "url"
    )
    list_filter = (
        "destination_type",
        "is_default",
        "deleted"
    )
    raw_id_fields = (
        "piece",
        "piece_dest",
        "behavior",
        "reply",
        "written",
        "message_link"
    )
    inlines = [AssignReplyInline, ConditionRuleDestinationInline]

    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "destination_type",
                    "piece",
                    "piece_dest",
                    "behavior",
                    "reply",
                    "written",
                    "message_link",
                    "url",
                    "is_default",
                    "order",
                    "deleted"
                )
            }),
        (
            "Additional Parameters",
            {
                "fields": ("addl_params",)
            }),
    )

    class Meta:
        verbose_name_plural = "Destinos"
        verbose_name = "Destino"
        ordering = ["order"]
