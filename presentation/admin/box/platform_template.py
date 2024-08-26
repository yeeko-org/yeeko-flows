from django.contrib import admin

from infrastructure.box.models import PlatformTemplate, TemplateParameter


class TemplateParameterInline(admin.TabularInline):
    model = TemplateParameter
    extra = 0
    raw_id_fields = ('extra',)


@admin.register(PlatformTemplate)
class PlatformTemplateAdmin(admin.ModelAdmin):

    list_display = (
        "template_id",
        "account",
        "name",
        "status",
        "category",
        "language",
        "description",
        "raw_template",
        "piece",
    )

    raw_id_fields = ('account',)
    list_filter = ('account', 'status', 'category', 'language')
    inlines = [TemplateParameterInline]


@admin.register(TemplateParameter)
class TemplateParameterAdmin(admin.ModelAdmin):

    list_display = (
        "template",
        "component_type",
        "key",
        "order",
        "extra",
        "default_value",
    )

    raw_id_fields = ('template', 'extra')
