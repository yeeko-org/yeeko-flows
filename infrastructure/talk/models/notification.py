from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from infrastructure.flow.models import Flow
from infrastructure.member.models import MemberAccount
from infrastructure.notification.models import Notification, NotificationTiming
from infrastructure.talk.models.extra import ExtraValue
from infrastructure.xtra.models import ClassifyExtra, Extra

DEFAULT_NOTIFICATION_LAPSE_MINUTES = getattr(
    settings, 'DEFAULT_NOTIFICATION_LAPSE_MINUTES', 30)


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
