import uuid as uuid_lib


from django.conf import settings
from django.db import models
from django.db.models import JSONField

from infrastructure.assign.models import ApplyBehavior
from infrastructure.notification.models import Notification
from infrastructure.service.models import InteractionType, ApiRecord
from infrastructure.box.models import (
    Fragment, MessageLink, PlatformTemplate, Reply, Written)
from infrastructure.tool.models import Behavior
from infrastructure.member.models import MemberAccount


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


CAN_DELETE_S3 = getattr(
    settings, "CAN_DELETE_AWS_STORAGE_FILES", False)


def get_media_in_upload_path(instance, filename):
    return f"media_in/{instance.member_account.account.pid}/{filename}"

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
    interaction_reply = models.ForeignKey(
        'Interaction', on_delete=models.CASCADE, blank=True, null=True,
        related_name='trigger_reply')

    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True)
    built_reply = models.ForeignKey(
        "BuiltReply", on_delete=models.CASCADE, blank=True, null=True,
        related_name='trigger_reply')
    written = models.ForeignKey(
        Written, on_delete=models.CASCADE, blank=True, null=True,
        related_name='trigger_reply')
    template = models.ForeignKey(
        PlatformTemplate, on_delete=models.CASCADE,
        blank=True, null=True, related_name='trigger_reply')

    message_link = models.ForeignKey(
        MessageLink, on_delete=models.CASCADE, blank=True, null=True,
        related_name='trigger_reply')

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, blank=True, null=True,
        related_name='trigger_reply')

    is_direct = models.BooleanField(
        default=False, help_text='Fue en respuesta clara')

    interaction: "Interaction"

    # fragment = models.ForeignKey(
    #     Fragment, on_delete=models.CASCADE, blank=True, null=True)
    # destination = models.ForeignKey(
    #     Destination, on_delete=models.CASCADE, blank=True, null=True)
    # reply = models.ForeignKey(
    #     Reply, on_delete=models.CASCADE, blank=True, null=True)
    # persona = models.ForeignKey(
    #     MemberAccount, on_delete=models.CASCADE, blank=True, null=True)
    # notification = models.ForeignKey(
    #     'Notification', on_delete=models.CASCADE, blank=True, null=True)

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
    raw_data_in = models.TextField(blank=True, null=True)
    raw_data = JSONField(blank=True, null=True, default=dict)
    media_in = models.FileField(
        upload_to=get_media_in_upload_path, blank=True, null=True)
    media_in_type = models.CharField(max_length=20, blank=True, null=True)
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

    def save(self, *args, **kwargs):
        if self.pk and CAN_DELETE_S3:
            try:
                old_instance = Interaction.objects.get(pk=self.pk)
                if old_instance.media_in and old_instance.media_in != self.media_in:
                    old_instance.media_in.delete(save=False)
            except Interaction.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if CAN_DELETE_S3:
            self.media_in.delete(save=False)

        super().delete(*args, **kwargs)

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
