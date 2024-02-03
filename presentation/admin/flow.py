from django.contrib import admin
from infrastructure.flow.models import Flow, CrateType, Crate


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('name', 'space', 'has_definitions', 'deleted')
    search_fields = ('name', 'space__title', 'description')
    list_filter = ('has_definitions', 'deleted')
    raw_id_fields = ('space',)

    fieldsets = (
        ('General', {
            'fields': ('name', 'space', 'description')
        }),
        ('Settings', {
            'fields': ('has_definitions', 'deleted')
        }),
    )

    class Meta:
        verbose_name_plural = "Flujos Conversacionales"
        verbose_name = "Flujo Conversacional"
        unique_together = ('name', 'space')


@admin.register(CrateType)
class CrateTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'description')
    search_fields = ('name', 'public_name', 'description')

    class Meta:
        verbose_name_plural = "Tipos de Caja"
        verbose_name = "Tipo de Caja"


@admin.register(Crate)
class CrateAdmin(admin.ModelAdmin):
    list_display = ('name', 'crate_type', 'flow', 'created', 'has_templates')
    search_fields = ('name', 'crate_type__name', 'flow__name', 'description')
    list_filter = ('created', 'has_templates')
    raw_id_fields = ('crate_type', 'flow')

    fieldsets = (
        ('General', {
            'fields': ('name', 'description', 'crate_type', 'flow', 'created')
        }),
        ('Settings', {
            'fields': ('has_templates',)
        }),
    )

    class Meta:
        verbose_name_plural = "Contenedores (campañas)"
        verbose_name = "Contenedor (campaña)"
        unique_together = ('name', 'crate_type')
