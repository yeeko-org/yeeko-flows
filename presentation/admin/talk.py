from django.contrib import admin

from infrastructure.talk.models import (
    Trigger, Interaction, BuiltReply, Event, ExtraValue
)


class InlineInteraction(admin.TabularInline):
    model = Interaction
    extra = 0
    raw_id_fields = ('trigger', 'member_account', 'persona')


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    # list_display = ('yk_participation', 'proposal_participation', 'behavior')
    list_display = ('display_trigger_info', 'is_direct')
    search_fields = (
        'interaction_reply__title', 'built_reply__title',
        'message_link__message')
    # raw_id_fields = ('yk_participation', 'proposal_participation', 'fragment',
    #                  'destination', 'reply', 'built_reply', 'behavior')
    inlines = (InlineInteraction,)

    def display_trigger_info(self, obj):
        return str(obj)

    display_trigger_info.short_description = 'Información del Origen'

    class Meta:
        verbose_name = 'Origen'
        verbose_name_plural = 'Orígenes'


class EventInline(admin.StackedInline):
    model = Event
    extra = 0
    raw_id_fields = ('api_request', 'interaction',)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('mid', 'interaction_type', 'is_incoming',
                    'member_account', 'created', 'trigger')
    search_fields = (
        'mid', 'interaction_type__name',
        'member_account__member__user__username')
    list_filter = ('interaction_type', 'is_incoming', 'created')
    raw_id_fields = (
        "trigger",
        "api_record_in",
        "api_record_out",
        "interaction_type",
        "member_account",
        "persona",
        "apply_behavior",
        "fragment",
    )
    inlines = (EventInline,)

    class Meta:
        verbose_name = 'Interacción'
        verbose_name_plural = 'Interacciones'


@admin.register(BuiltReply)
class BuiltReplyAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'interaction', 'is_for_reply',
                    'is_for_write', 'reply')
    search_fields = ('uuid', 'interaction__mid', 'reply__title')
    list_filter = ('is_for_reply', 'is_for_write', 'reply')

    class Meta:
        verbose_name = 'Respuesta construida'
        verbose_name_plural = 'Respuestas construidas'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'api_request', 'timestamp',
                    'emoji', 'interaction', 'date')
    search_fields = ('event_name', 'interaction__mid')
    list_filter = ('event_name', 'api_request', 'timestamp',
                   'emoji', 'interaction', 'date')

    class Meta:
        verbose_name = 'Evento de interacción'
        verbose_name_plural = 'Eventos de interacción'
        unique_together = ('event_name', 'interaction', 'emoji')


@admin.register(ExtraValue)
class ExtraValueAdmin(admin.ModelAdmin):
    list_display = ('extra', 'member', 'origin',
                    'modified', 'value', 'list_by')
    search_fields = ('extra__name', 'member__user__username')
    list_filter = ('extra', 'member', 'origin', 'modified', 'list_by')
    filter_horizontal = ('interactions',)
    raw_id_fields = ('extra', 'member', 'interactions')

    class Meta:
        verbose_name = 'Valor extra'
        verbose_name_plural = 'Valores extra'
        unique_together = ('extra', 'member', 'list_by')
        ordering = ['-modified']
