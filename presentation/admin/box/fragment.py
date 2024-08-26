from django.contrib import admin
from infrastructure.assign.models import ParamValue
from infrastructure.box.models import Fragment, Reply
from presentation.admin.box.inline import ConditionRuleInline


class ConditionRuleFragmentInline(ConditionRuleInline):
    fk_name = 'fragment'


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
    inlines = [ReplyInline, ParamValueInline, ConditionRuleFragmentInline]

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
