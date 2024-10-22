from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from infrastructure.flow.models import Flow
from infrastructure.member.models import MemberAccount
from infrastructure.notification.models import Notification, NotificationTiming
from infrastructure.talk.models.extra import ExtraValue
from infrastructure.talk.models.models import Interaction
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
        degradation = getattr(self.actual_timing, "degradation_to_disinterest")
        if not degradation:
            return

        self.member_account.degrade_interest_degreee(degradation)

    def set_controler(self):
        if self.controller:
            return

        extra_controler, _ = Extra.objects.get_or_create(
            name=self.notification.name+"_controler",
            space=self.member_account.account.space,
            defaults={
                "classify_id": "Notification",
                "flow_id": "Notification",
                "format": "int"
            }
        )

        self.controller, _ = ExtraValue.objects.get_or_create(
            extra=extra_controler,
            member=self.member_account.member,
        )

    def get_timing_minuts(
            self, timing: NotificationTiming | None,
            last_interaction_out: Interaction | None = None
    ) -> int:
        """
        Calculates the remaining time in minutes for the next notification.

        If there is a last_interaction_out, ajust the timing_minuts to the
        min_gap_last_interaction_out. Get the elapsed time and if it is greater
        than the timing_minuts, return 0, else return the remaining time.
        """
        if timing:
            timing_minuts = timing.timing
        else:
            timing_minuts = DEFAULT_NOTIFICATION_LAPSE_MINUTES
        if not last_interaction_out:
            return timing_minuts

        min_gap_last_out = self.notification.min_gap_last_interaction_out
        if timing_minuts < min_gap_last_out:
            timing_minuts = min_gap_last_out

        elapsed_time = timezone.now() - last_interaction_out.created
        elapsed_minutes = int(elapsed_time.total_seconds() / 60)

        if elapsed_minutes > timing_minuts:
            return 0
        else:
            remaining_time = timing_minuts - elapsed_minutes
            return remaining_time

    def can_set_timing_index(self, timing_index) -> bool:
        if self.notification.unlimited_timing:
            return True
        elif self.notification.limit_timing:
            return self.notification.limit_timing > timing_index
        else:
            return self.notification.timings.count() > timing_index

    def get_next_timing_index(self) -> int | None:

        actual_timing_index = self.controller.get_value()
        if not isinstance(actual_timing_index, int):
            raise ValueError(
                f"Controler value is not a number: {actual_timing_index}")
        next_timing_index = actual_timing_index + 1

        if self.can_set_timing_index(next_timing_index):
            return next_timing_index
        else:
            return None

    def set_index_into_controler(
        self, timing_index: int, last_interaction_out: Interaction | None = None
    ):

        self.set_controler()
        self.controller.set_value(timing_index)
        self.controller.origin = "notification"
        self.controller.save()

        timing = self.notification.get_timing_or_last(timing_index)
        timing_minuts = self.get_timing_minuts(timing, last_interaction_out)
        self.next_at = timezone.now() + timedelta(minutes=timing_minuts)

        self.actual_timing = timing

        next_timing_index = self.get_next_timing_index()
        if next_timing_index:
            self.next_timing = self.notification.get_timing_or_last(
                next_timing_index)

        self.save()

    def set_init_controler(self, last_interaction_out: Interaction | None = None):
        self.set_index_into_controler(0, last_interaction_out)

    def set_next_controler(
            self, degrade_interest: bool = True,
            last_interaction_out: Interaction | None = None
    ):
        next_timing_index = self.get_next_timing_index()
        if next_timing_index is None:
            return

        if degrade_interest:
            self.degrade_interest_degreee()

        self.set_index_into_controler(next_timing_index, last_interaction_out)

    def set_parameters(self, parameters_data: dict):

        parameter_extra, _ = Extra.objects.get_or_create(
            name=self.notification.name + "_parameters",
            space=self.member_account.account.space,
            defaults={
                "classify_id": "Notification",
                "flow_id": "Notification",
                "format": "json"
            }
        )

        self.parameters, _ = ExtraValue.objects.get_or_create(
            extra=parameter_extra,
            member=self.member_account.member,
            list_by=self.controller,
        )

        self.parameters.set_value(parameters_data)
        self.parameters.origin = "notification"
        self.parameters.save()

    def next_at_not_chosen(self, save: bool = True):
        next_at_minutes = self.notification.not_choisen_reconsidered_time
        self.next_at = timezone.now() + timedelta(minutes=next_at_minutes)
        if save:
            self.save()

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
