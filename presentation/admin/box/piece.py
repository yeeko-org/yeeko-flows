from django.contrib import admin
from infrastructure.box.models import Piece, Fragment
from presentation.admin.box.inline import AssignInline, DestinationInline


class AssignPieceInline(AssignInline):
    fk_name = 'piece'


class DestinationPieceInline(DestinationInline):
    fk_name = 'piece'


class FragmentInline(admin.TabularInline):
    model = Fragment
    extra = 0
    show_change_link = True
    fk_name = 'piece'
    raw_id_fields = ('behavior', 'embedded_piece', )
    fields = [
        "fragment_type",
        "piece",
        "order",
        "body",
        "behavior",
        "deleted",
        "file",
        "media_url",
        "media_type",
        "header",
        "footer",
        "reply_title",
        "embedded_piece",
    ]


@admin.register(Piece)
class PieceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'crate', 'behavior', 'default_extra', 'insistent',
        'mandatory', 'order_in_crate', 'deleted')
    search_fields = ('name', 'crate__name',
                     'behavior__name', 'default_extra__name')
    list_filter = ('insistent', 'mandatory', 'deleted',
                   'crate', 'behavior', 'default_extra')
    raw_id_fields = ('crate', 'behavior', 'default_extra')

    inlines = [FragmentInline, DestinationPieceInline, AssignPieceInline]

    fieldsets = (
        ('General', {
            'fields': ('name', 'description', 'crate', 'behavior', 'default_extra',
                       'insistent', 'mandatory', 'order_in_crate', 'deleted')
        }),
        ('Configuration', {
            'fields': ('config',)
        }),
        ('Written Option', {
            'fields': ('written',)
        }),
    )

    class Meta:
        verbose_name_plural = "Piezas (Mensajes)"
        verbose_name = "Pieza (Mensaje)"
        ordering = ['order_in_crate']
