from django.contrib import admin

from infrastructure.service.models import ApiRecord, InteractionType, Platform


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'with_users', 'internal')
    list_filter = ('with_users', 'internal')
    search_fields = ('name', 'public_name', 'description')

    fieldsets = (
        ('General', {
            'fields': (
                'name', 'public_name', 'description', 'config', 'with_users',
                'id_field', 'internal'
            )
        }),
        ('Appearance', {
            'fields': ('color', 'icon', 'image')
        }),
        ('Configuration', {
            'fields': ('config_by_member',)
        }),
    )

    class Meta:
        verbose_name = "Plataforma con API e interacción"
        verbose_name_plural = "Plataformas con API e interacción"


@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'way', 'group_type')
    list_filter = ('way', 'group_type')
    search_fields = ('name', 'public_name')

    fieldsets = (
        ('General', {
            'fields': ('name', 'public_name', 'way', 'group_type')
        }),
    )

    class Meta:
        verbose_name = 'Tipo de interacción'
        verbose_name_plural = 'Tipos de interacción'


@admin.register(ApiRecord)
class ApiRecordAdmin(admin.ModelAdmin):
    list_display = ('platform', 'interaction_type',
                    'is_incoming', 'success', 'created')
    list_filter = ('platform', 'interaction_type', 'is_incoming', 'success')
    search_fields = ('platform__name', 'interaction_type__name', 'created')

    fieldsets = (
        ('General', {
            'fields': ('platform', 'body', 'interaction_type', 'is_incoming')
        }),
        ('Response', {
            'fields': ('response_status', 'response_body')
        }),
        ('Error Details', {
            'fields': ('error_text', 'errors')
        }),
        ('Related', {
            'fields': ('repeated',)
        }),
        ('Timestamps', {
            'fields': ('created', 'datetime')
        }),
        ('Flags', {
            'fields': ('success',)
        }),
    )

    readonly_fields = ('created', 'datetime')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return list(self.readonly_fields) + ['platform', 'interaction_type', 'is_incoming']
        return self.readonly_fields
