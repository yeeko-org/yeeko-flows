from django.contrib import admin
from infrastructure.assign.models import ParamValue
from infrastructure.box.models import (
    Written, Piece, Fragment, Reply, MessageLink, Destination
)


class DestinationWriteInline(admin.TabularInline):
    model = Destination
    extra = 0
    show_change_link = True
    fk_name = 'written'
    fields = (
        'destination_type', 'piece_dest', 'behavior', 'reply', 'url',
        'addl_params', 'is_default', 'order', 'deleted'
    )


@admin.register(Written)
class WrittenAdmin(admin.ModelAdmin):
    list_display = ('id', 'extra', 'collection', 'available')
    search_fields = ('extra__name', 'collection__name')
    list_filter = ('available', 'extra', 'collection')
    raw_id_fields = ('extra', 'collection')
    inlines = [DestinationWriteInline]

    fieldsets = (
        ('General', {
            'fields': ('extra', 'collection', 'available')
        }),
    )

    class Meta:
        verbose_name_plural = "Opciones escritas"
        verbose_name = "Opción escrita"


class FragmentInline(admin.TabularInline):
    model = Fragment
    extra = 0
    show_change_link = True
    fk_name = 'piece'


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

    inlines = [FragmentInline]

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


class ParamValueInline(admin.TabularInline):
    model = ParamValue
    extra = 0
    show_change_link = True
    fk_name = 'fragment'
    fields = ('parameter', 'value')
    classes = ['collapse']


class ReplyInline(admin.TabularInline):
    model = Reply
    extra = 0
    show_change_link = True
    fk_name = 'fragment'


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin):
    list_display = ('piece', 'behavior', 'order', 'deleted')
    search_fields = ('piece__name', 'behavior__name')
    list_filter = ('behavior', 'deleted')
    raw_id_fields = ('piece', 'behavior',  'embedded_piece')
    inlines = [ReplyInline, ParamValueInline]

    fieldsets = (
        ('General', {
            'fields': ('piece',  'order', 'deleted')
        }),

        ('Message', {
            'fields': ('header', 'body', 'footer', 'reply_title')
        }),
        ('Media', {
            'fields': ('file', 'media_url', 'media_type'),
            'classes': ('collapse',)
        }),
        ('Embedded Piece', {
            'fields': ('embedded_piece',),
            'classes': ('collapse',)
        }),
        ('Behavior', {
            'fields': ('behavior',),
            'classes': ('collapse',)
        }),
        ('Additional Parameters', {
            'fields': ('addl_params',),
            'classes': ('collapse',)
        }),
    )

    class Meta:
        verbose_name_plural = "Fragmentos"
        verbose_name = "Fragmento"
        ordering = ['order']


class DestinationReplyInline(admin.TabularInline):
    model = Destination
    extra = 0
    show_change_link = True
    fk_name = 'reply'
    fields = (
        'destination_type',  'piece_dest', 'behavior', 'url',
        'addl_params', 'is_default', 'order', 'deleted'
    )


@ admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('fragment', 'title', 'order', 'is_jump', 'deleted')
    search_fields = ('fragment__title', 'title', 'description', )
    list_filter = ('is_jump', 'deleted', 'use_piece_config', 'fragment')
    raw_id_fields = ('fragment',)
    inlines = [DestinationReplyInline]

    fieldsets = (
        ('General', {
            'fields': (
                'fragment', 'title', 'is_section', 'description', 'large_title',
                'order', 'is_jump', 'use_piece_config', 'deleted'
            )
        }),
        ('Context for chatGPT', {
            'fields': ('context',)
        }),
        ('Additional Parameters', {
            'fields': ('addl_params',)
        }),
    )

    class Meta:
        verbose_name_plural = "Respuestas (Botones)"
        verbose_name = "Respuesta (Botón)"
        ordering = ['order']


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

    class Meta:
        verbose_name_plural = "Message Links"
        verbose_name = "Message Link"


@ admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = (
        'destination_type', 'piece', 'behavior', 'reply', 'written',
        'message_link', 'url', 'is_default', 'order', 'deleted')
    search_fields = (
        'piece__name', 'behavior__name', 'reply__title',
        'written__extra__name', 'message_link__message', 'url')
    list_filter = ('destination_type', 'is_default', 'deleted')
    raw_id_fields = ('piece', 'piece_dest', 'behavior',
                     'reply', 'written', 'message_link')

    fieldsets = (
        ('General', {
            'fields': (
                'destination_type', 'piece', 'piece_dest', 'behavior', 'reply',
                'written', 'message_link', 'url', 'is_default', 'order',
                'deleted'
            )
        }),
        ('Additional Parameters', {
            'fields': ('addl_params',)
        }),
    )

    class Meta:
        verbose_name_plural = "Destinos"
        verbose_name = "Destino"
        ordering = ['order']
