from django.contrib import admin
from infrastructure.box.models import MessageLink
from presentation.admin.box.inline import DestinationInline


class DestinationPieceInline(DestinationInline):
    fk_name = 'message_link'


@ admin.register(MessageLink)
class MessageLinkAdmin(admin.ModelAdmin):
    list_display = ('account', 'link', 'message')
    search_fields = ('account__space__title',
                     'account__platform__public_name', 'link', 'message')
    raw_id_fields = ('account',)

    fieldsets = (
        ('General', {
            'fields': ('account', 'link', 'message')
        }),
        ('QR Codes', {
            'fields': ('qr_code_png', 'qr_code_svg')
        }),
    )

    inlines = [DestinationPieceInline]

    class Meta:
        verbose_name_plural = "Message Links"
        verbose_name = "Message Link"
