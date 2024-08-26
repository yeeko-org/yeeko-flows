from django.contrib import admin
from infrastructure.box.models import Reply

from presentation.admin.box.inline import (
    AssignInline, ConditionRuleInline, DestinationInline)


class AssignReplyInline(AssignInline):
    fk_name = 'reply'


class ConditionRuleReplyInline(ConditionRuleInline):
    fk_name = 'reply'


class DestinationReplyInline(DestinationInline):
    fk_name = 'reply'


@ admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('fragment', 'title', 'order', 'is_jump', 'deleted')
    search_fields = ('fragment__title', 'title', 'description', )
    list_filter = ('is_jump', 'deleted', 'use_piece_config', 'fragment')
    raw_id_fields = ('fragment',)
    inlines = [
        DestinationReplyInline, AssignReplyInline, ConditionRuleReplyInline]

    fieldsets = (
        ('General', {
            'fields': (
                'fragment', 'title', 'is_header_section', 'description', 'large_title',
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
