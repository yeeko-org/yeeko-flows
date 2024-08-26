
from django.contrib import admin

from infrastructure.tool.models import Collection, Behavior, Parameter


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'is_custom',
                    'open_available', 'app_label')
    search_fields = ('name', 'public_name', 'app_label')
    list_filter = ('is_custom', 'open_available', 'spaces')
    raw_id_fields = ('spaces',)

    fieldsets = (
        ('General', {
            'fields': ('name', 'public_name', 'is_custom', 'open_available',
                       'app_label')
        }),
        ('Spaces', {
            'fields': ('spaces',)
        }),
    )

    class Meta:
        verbose_name_plural = "Colecciones"
        verbose_name = "Colección"


class ParameterInline(admin.TabularInline):
    model = Parameter
    extra = 0
    show_change_link = True


@admin.register(Behavior)
class BehaviorAdmin(admin.ModelAdmin):
    list_display = ('name', 'collection', 'can_piece',
                    'can_destination', 'in_code', 'interaction_type')
    search_fields = ('name', 'collection__name', 'interaction_type__name')
    list_filter = ('can_piece', 'can_destination', 'in_code',
                   'collection', 'interaction_type')
    raw_id_fields = ('collection', 'interaction_type')

    fieldsets = (
        ('General', {
            'fields': ('name', 'collection', 'can_piece', 'can_destination',
                       'in_code')
        }),
        ('Optional', {
            'fields': ('interaction_type',)
        }),
    )
    inlines = [ParameterInline]

    class Meta:
        verbose_name_plural = "Funciones"
        verbose_name = "Función"


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'behavior', 'public_name', 'is_required', 'data_type',
        'customizable_by_piece', 'order', 'deleted')
    search_fields = ('name', 'behavior__name',
                     'public_name', 'data_type', 'model')
    list_filter = (
        'is_required', 'data_type', 'customizable_by_piece', 'behavior',
        'model', 'deleted')
    raw_id_fields = ('behavior',)

    fieldsets = (
        ('General', {
            'fields': ('name', 'behavior', 'public_name', 'description',
                       'is_required', 'default_value', 'data_type')
        }),
        ('Customization', {
            'fields': ('customizable_by_piece', 'addl_config', 'rules')
        }),
        ('Additional', {
            'fields': ('model', 'order', 'addl_dashboard', 'deleted')
        }),
    )

    class Meta:
        verbose_name_plural = "Parámetros"
        verbose_name = "Parámetro"
        ordering = ['order']
