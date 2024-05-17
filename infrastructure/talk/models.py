from django.db import models
import uuid as uuid_lib
from django.db.models import JSONField

from infrastructure.assign.models import ApplyBehavior
from infrastructure.service.models import InteractionType, ApiRecord
from infrastructure.box.models import Fragment, MessageLink, Reply
from infrastructure.xtra.models import Extra
from infrastructure.member.models import MemberAccount, Member

EVENT_NAME_CHOICES = (
    ('received', 'received'),
    ('sent', 'sent'),
    ('delivered', 'delivered'),
    ('read', 'read'),
    # ('postback', 'postback'),
    ('optin', 'optin'),
    ('referral', 'referral'),
    ('failed', 'failed'),
    ('deleted', 'deleted'),
    ('warning', 'warning'),
    ('reaction', 'reaction'),
)

ORIGIN_CHOICES = (
    ("payload", "Payload"),
    ("written", "Escrito"),
    ("dictionary", "Diccionario"),
    ("assigned", "Asignado"),
    ("unknown", "Desconocido"),
)

# class RequestCategory(models.Model):
#     name = models.CharField(max_length=50, primary_key=True)
#     public_name = models.CharField(max_length=120, blank=True, null=True)
#     way = models.CharField(max_length=5, choices=WAY_CHOICES)
#     is_attachment = models.BooleanField(default=False)
#     description = models.CharField(max_length=255, blank=True, null=True)
#
#     def __str__(self):
#         return f"{self.name} - {self.way} ({self.public_name})"
#
#     class Meta:
#         verbose_name = 'Categoría de solicitud'
#         verbose_name_plural = 'Categorías de solicitud'


class Trigger(models.Model):
    # yk_participation = models.ForeignKey(
    #     YkParticipation, on_delete=models.CASCADE, blank=True, null=True)
    # proposal_participation = models.ForeignKey(
    #     ProposalParticipation, on_delete=models.CASCADE, blank=True, null=True)
    # behavior = models.ForeignKey(
    #     Behavior, on_delete=models.CASCADE, blank=True, null=True)
    # fragment = models.ForeignKey(
    #     Fragment, on_delete=models.CASCADE, blank=True, null=True)
    # destination = models.ForeignKey(
    #     Destination, on_delete=models.CASCADE, blank=True, null=True)
    # reply = models.ForeignKey(
    #     Reply, on_delete=models.CASCADE, blank=True, null=True)
    interaction_reply = models.ForeignKey(
        'Interaction', on_delete=models.CASCADE, blank=True, null=True,
        related_name='trigger_reply')
    built_reply = models.ForeignKey(
        "BuiltReply", on_delete=models.CASCADE, blank=True, null=True)
    message_link = models.ForeignKey(
        MessageLink, on_delete=models.CASCADE, blank=True, null=True)
    # persona = models.ForeignKey(
    #     MemberAccount, on_delete=models.CASCADE, blank=True, null=True)
    # notification = models.ForeignKey(
    #     'Notification', on_delete=models.CASCADE, blank=True, null=True)
    is_direct = models.BooleanField(
        default=False, help_text='Fue en respuesta clara')

    def __str__(self):
        fields_of_model = self._meta.get_fields()
        for field in fields_of_model:
            if getattr(self, field.name):
                str_field = getattr(self, field.name).__str__()
                return f"{field.name}: {str_field}"

    class Meta:
        verbose_name = 'Origen'
        verbose_name_plural = 'Orígenes'


class Interaction(models.Model):
    mid = models.CharField(max_length=200, primary_key=True)
    interaction_type = models.ForeignKey(
        InteractionType, on_delete=models.CASCADE)
    is_incoming = models.BooleanField(default=True)
    member_account = models.ForeignKey(
        MemberAccount, on_delete=models.CASCADE)
    trigger = models.OneToOneField(
        Trigger, on_delete=models.CASCADE,
        blank=True, null=True, related_name='interaction')
    api_record_in = models.ManyToManyField(
        ApiRecord, blank=True, related_name='api_records_in'
    )
    api_record_out = models.OneToOneField(
        ApiRecord, on_delete=models.CASCADE, related_name='api_records_out'
    )
    persona = models.ForeignKey(
        MemberAccount, on_delete=models.CASCADE,
        blank=True, null=True, related_name='persona')
    created = models.DateTimeField(auto_now_add=True)
    timestamp = models.IntegerField(
        verbose_name='Timestamp según plataforma', blank=True, null=True)
    # reply_from = models.ForeignKey(
    #     'self', on_delete=models.CASCADE,
    #     blank=True, null=True, related_name='reply_from')
    raw_payload = models.TextField(blank=True, null=True)
    reference = JSONField(blank=True, null=True)
    # commit_simple = JSONField(blank=True, null=True, blank=True, null=True)
    # write_destination = models.ForeignKey(
    #     Destination, on_delete=models.CASCADE,
    #     blank=True, null=True, related_name='write_destination')
    apply_behavior = models.ForeignKey(
        ApplyBehavior, on_delete=models.CASCADE,
        blank=True, null=True, related_name='apply_behavior')
    # destination = models.ForeignKey(
    #     Destination, on_delete=models.CASCADE,
    #     blank=True, null=True, related_name='destination')
    fragment = models.ForeignKey(
        Fragment, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.interaction_type.name} - {self.mid}"

    class Meta:
        verbose_name = 'Interacción'
        verbose_name_plural = 'Interacciones'
        ordering = ['-created']


class BuiltReply(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    interaction = models.ForeignKey(
        Interaction, on_delete=models.CASCADE, blank=True, null=True)

    # RICK 5: No me acuerdo para qué era este campo, agregué el is_for_write
    is_for_reply = models.BooleanField(default=False)
    is_for_write = models.BooleanField(default=False)

    params = JSONField(blank=True, null=True)
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE, blank=True, null=True)

    payload = models.TextField(
        blank=True, null=True, verbose_name='Payload (old)')
    # destination = models.ForeignKey(
    #     Destination, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.interaction} - {self.uuid}"

    class Meta:
        verbose_name = 'Respuesta construida'
        verbose_name_plural = 'Respuestas construidas'


class Event(models.Model):
    event_name = models.CharField(
        max_length=20, choices=EVENT_NAME_CHOICES)
    api_request = models.ForeignKey(
        ApiRecord, on_delete=models.CASCADE, blank=True, null=True)
    timestamp = models.IntegerField(blank=True, null=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)
    interaction = models.ForeignKey(
        Interaction, on_delete=models.CASCADE)
    date = models.DateTimeField()
    content = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.interaction} - {self.event_name}"

    class Meta:
        verbose_name = 'Evento de interacción'
        verbose_name_plural = 'Eventos de interacción'
        unique_together = ('event_name', 'interaction', 'emoji')


class ExtraValue(models.Model):
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE)
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, blank=True, null=True,
        related_name='extra_values')
    interactions = models.ManyToManyField(Interaction, blank=True)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    modified = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    value = models.TextField(blank=True, null=True)
    list_by = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True,
        related_name='children')
    value_bool = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return f"{self.extra} - {self.value or self.value_bool}"

    class Meta:
        verbose_name = 'Valor extra'
        verbose_name_plural = 'Valores extra'
        unique_together = ('extra', 'member', 'list_by')
        ordering = ['-modified']

# class ApiError(models.Model):
#     interaction = models.ForeignKey(
#         Interaction, on_delete=models.CASCADE, blank=True, null=True)
#     api_request = models.ForeignKey(
#         ApiRecord, on_delete=models.CASCADE, blank=True, null=True)
#     text = models.TextField(blank=True, null=True)
#     errors = JSONField(blank=True, null=True)
#
#     def __str__(self):
#         return f"{self.interaction} - {self.api_request}"
#
#     class Meta:
#         verbose_name = 'Error de API'
#         verbose_name_plural = 'Errores de API'
