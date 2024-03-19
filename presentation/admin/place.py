from django.contrib import admin
from infrastructure.place.models import Space, Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('pid', 'space', 'platform', 'title', 'active')
    search_fields = (
        'pid', 'space__title',  'platform__public_name', 'title',
        'platform__title'
    )
    list_filter = ('active', 'init_text_response',
                   'text_response', 'payload_response', 'notif_enabled')
    raw_id_fields = ('space', 'platform')

    fieldsets = (
        ('General', {
            'fields': ('pid', 'space', 'platform', 'title', 'token', 'config', 'active')
        }),
        ('Response Settings', {
            'fields': ('init_text_response', 'text_response', 'payload_response')
        }),
        ('Notification Settings', {
            'fields': ('notif_enabled',)
        }),
    )

    class Meta:
        verbose_name_plural = "Cuentas por plataforma"
        verbose_name = "Cuenta por plataforma"


class AccountInline(admin.StackedInline):
    model = Account
    extra = 0
    show_change_link = True


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'bot_name', 'test')
    search_fields = ('title', 'created', 'bot_name')
    list_filter = ('test',)
    date_hierarchy = 'created'
    readonly_fields = ('created',)
    inlines = [AccountInline]

    fieldsets = (
        ('General', {
            'fields': ('title', 'created', 'bot_name', 'test')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Parameters', {
            'fields': ('params',)
        }),
    )

    class Meta:
        verbose_name_plural = "Espacios (Páginas)"
        verbose_name = "Espacio (Página)"
