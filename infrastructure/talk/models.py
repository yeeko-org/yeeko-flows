import json
import re
import uuid as uuid_lib

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from infrastructure.assign.models import ApplyBehavior
from infrastructure.flow.models import Flow
from infrastructure.notification.models import Notification, NotificationTiming
from infrastructure.service.models import InteractionType, ApiRecord
from infrastructure.box.models import Fragment, MessageLink, PlatformTemplate, Reply, Written
from infrastructure.tool.models import Behavior
from infrastructure.xtra.models import ClassifyExtra, Extra
from infrastructure.member.models import MemberAccount, Member
from utilities.json_compatible import ensure_json_compatible

DEFAULT_NOTIFICATION_LAPSE_MINUTES = getattr(
    settings, 'DEFAULT_NOTIFICATION_LAPSE_MINUTES', 30)

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
    ("notification", "Notificación"),
    ("unknown", "Desconocido"),
)

CAN_DELETE_S3 = getattr(
    settings, "CAN_DELETE_AWS_STORAGE_FILES", False)

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


def get_media_in_upload_path(instance, filename):
    return f"media_in/{instance.member_account.account.pid}/{filename}"


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

    def __str__(self):
        return f"{self.extra} - {self.value or 'True'}"

    def get_value(self):
        if not self.value:
            return None

        if self.extra.format_id == 'json':
            try:
                return json.loads(self.value or "{}")
            except json.JSONDecodeError:
                return {}

        if self.extra.format_id == 'int':
            try:
                return int(self.value)
            except ValueError:
                return 0

        return self.value

    def set_value(self, value):
        if self.extra.format_id == 'json':
            if not isinstance(value, (dict, list)):
                value = {
                    "value": value
                }
            try:
                self.value = json.dumps(value)
            except json.JSONDecodeError as e:
                value = {
                    "data": ensure_json_compatible(value),
                    "set_value_error": str(e)
                }
                self.value = json.dumps(value)
        else:
            self.value = str(value)

    def addition(self, adder: int = 1, save: bool = True):
        if not self.extra.format_id == 'int':
            raise ValueError(
                f'Just for int format, extra format is {self.extra.format_id}')

        if not self.value:
            self.value = "0"

        if not bool(re.fullmatch(r"-?\d+", self.value)):
            raise ValueError(f'Value is not a number: {self.value}')

        self.value = str(int(self.value) + adder)

        if save:
            self.save()

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


class NotificationMember(models.Model):
    member_account = models.ForeignKey(
        MemberAccount, on_delete=models.CASCADE)
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE)

    controller = models.ForeignKey(
        ExtraValue, on_delete=models.CASCADE, related_name='controller',
        blank=True)
    parameters = models.ForeignKey(
        ExtraValue, on_delete=models.CASCADE, related_name='parameters',
        blank=True)

    last_sent = models.DateTimeField(auto_now=True)
    next_at = models.DateTimeField(blank=True, null=True)

    actual_timing = models.ForeignKey(
        NotificationTiming, on_delete=models.CASCADE, blank=True, null=True,
        related_name='actual_timings')
    next_timing = models.ForeignKey(
        NotificationTiming, on_delete=models.CASCADE, blank=True, null=True,
        related_name='next_timings')

    def degrade_interest_degreee(self):
        if not self.actual_timing or not self.actual_timing.degradation_to_disinterest:
            return

        degradation = self.actual_timing.degradation_to_disinterest / 100
        self.member_account.interest_degree -= int(
            degradation * self.member_account.interest_degree)
        self.member_account.save()

    def set_controler(self):
        if self.controler:
            return

        try:
            extra_controler = Extra.objects.get(
                name=self.notification.name+"_controler",
                space=self.member_account.account.space)
        except Extra.DoesNotExist:
            # create the classify by init_data
            classify_extra, _ = ClassifyExtra.objects\
                .get_or_create(name="notification")

            flow, _ = Flow.objects.get_or_create(
                name="notification",
                space=self.member_account.account.space
            )

            extra_controler = Extra.objects.create(
                name=self.notification.name+"_controler",
                classify=classify_extra,
                space=self.member_account.account.space,
                flow=flow,
                format="int"
            )

            self.controler, _ = ExtraValue.objects.get_or_create(
                extra=extra_controler,
                member=self.member_account.member,
            )

    def set_init_controler(self):
        timing = self.notification.get_timing_or_last(0)

        if timing:
            timing_minuts = timing.timing
        else:
            timing_minuts = DEFAULT_NOTIFICATION_LAPSE_MINUTES

        self.set_controler()

        self.controler.set_value(0)
        self.controler.origin = "notification"
        self.controler.save()

        self.next_at = timezone.now() + timedelta(minutes=timing_minuts)
        self.actual_timing = timing
        self.next_timing = self.notification.get_timing_or_last(1)
        self.save()

    def set_next_controler(self):
        self.degrade_interest_degreee()

        if self.next_timing:
            timing_minuts = self.next_timing.timing
        else:
            timing_minuts = DEFAULT_NOTIFICATION_LAPSE_MINUTES

        self.set_controler()
        index_controler = self.controler.get_value()  # type: ignore
        if not isinstance(index_controler, int):
            raise ValueError(
                f"Controler value is not a number: {self.controler.get_value()}")

        self.controler.set_value(index_controler + 1)
        self.controler.origin = "notification"
        self.controler.save()

        self.next_at = timezone.now() + timedelta(minutes=timing_minuts)
        self.actual_timing = self.next_timing
        self.next_timing = self.notification.get_timing_or_last(
            index_controler + 1)
        self.save()

    def set_parameters(self, parameters: dict):
        try:
            parameter_extra = Extra.objects.get(
                name=self.notification.name + "_parameters",
                space=self.member_account.account.space)
        except Extra.DoesNotExist:
            parameter_extra = Extra.objects.create(
                name=self.notification.name + "_parameters",
                classify=self.controler.extra.classify,
                space=self.controler.extra.space,
                flow=self.controler.extra.flow,
                format="json"
            )

        self.parameters, _ = ExtraValue.objects.get_or_create(
            extra=parameter_extra,
            member=self.member_account.member,
            list_by=self.controler,
        )

        self.parameters.set_value(parameters)
        self.parameters.origin = "notification"
        self.parameters.save()

    def next_at_not_chosen(self):
        next_at_minutes = self.notification.not_choisen_reconsidered_time
        self.next_at = timezone.now() + timedelta(minutes=next_at_minutes)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
