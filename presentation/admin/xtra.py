from django.contrib import admin
from infrastructure.xtra.models import ClassifyExtra, Format, Extra, PresetValue


@admin.register(ClassifyExtra)
class ClassifyExtraAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'only_developers',
                    'user_visible', 'is_public', 'order', 'icon', 'pixel_excel')
    search_fields = ('name', 'public_name', 'description',
                     'user_visible', 'icon')
    list_filter = ('only_developers', 'is_public')

    fieldsets = (
        ('General', {
            'fields': ('name', 'public_name', 'description', 'only_developers')
        }),
        ('Visibility', {
            'fields': ('user_visible', 'is_public')
        }),
        ('Order and Icon', {
            'fields': ('order', 'icon')
        }),
        ('Pixel Excel', {
            'fields': ('pixel_excel',)
        }),
        ('Settings', {
            'fields': ('settings',)
        }),
    )

    class Meta:
        verbose_name_plural = "Clasificaciones de Extras"
        verbose_name = "Clasificación de Extras"
        ordering = ['order']


@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'javascript_name', 'python_name')
    search_fields = ('name', 'public_name', 'javascript_name', 'python_name')

    fieldsets = (
        ('General', {
            'fields': ('name', 'public_name', 'javascript_name', 'python_name')
        }),
        ('Parameters', {
            'fields': ('params',)
        }),
    )

    class Meta:
        verbose_name_plural = "Formatos"
        verbose_name = "Formato"


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display = ('name', 'classify', 'space', 'flow', 'format', 'deleted')
    search_fields = ('name', 'classify__name', 'space__title',
                     'flow__name', 'format__name', 'description')
    list_filter = ('classify', 'space', 'format', 'deleted')
    raw_id_fields = ('classify', 'space', 'flow', 'format')

    fieldsets = (
        ('General', {
            'fields': ('name', 'classify', 'space', 'flow', 'format',
                       'description', 'deleted')
        }),
        ('Parameters', {
            'fields': ('params',)
        }),
    )

    class Meta:
        verbose_name_plural = "Extras"
        verbose_name = "Extra"


@admin.register(PresetValue)
class PresetValueAdmin(admin.ModelAdmin):
    list_display = ('extra', 'value', 'deleted')
    search_fields = ('extra__name', 'value')
    list_filter = ('extra', 'deleted')
    raw_id_fields = ('extra',)

    fieldsets = (
        ('General', {
            'fields': ('extra', 'value', 'deleted')
        }),
    )

    class Meta:
        verbose_name_plural = "Valores Predefinidos de Extras"
        verbose_name = "Valor Predefinido de Extras"
