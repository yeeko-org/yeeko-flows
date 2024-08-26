from django.db import models

from infrastructure.place.models import Account


class Notification(models.Model):
    name = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name='notifications',
        blank=True, null=True)

    limit_timing = models.IntegerField(blank=True, null=True)
    unlimited_timing = models.BooleanField(default=False)

    not_choisen_reconsidered_time = models.IntegerField(
        default=120, help_text='Minutes, for not chosen, not for failed')

    timings: models.QuerySet["NotificationTiming"]

    def __str__(self):
        return self.name

    def get_destinations(self):
        return (
            self.destinations.filter(deleted=False)  # type: ignore
            .order_by('order')
        )

    def get_timing_or_last(self, timing_index: int) -> "NotificationTiming | None":
        try:
            return self.timings.order_by('index')[timing_index]
        except IndexError:
            return self.timings.order_by('index').last()

    def set_order_to_timing(self):
        for index, timing in enumerate(self.timings.order_by("order")):
            timing.index = index
            timing.save()

    class Meta:
        verbose_name = 'Notification Type'
        verbose_name_plural = 'Notification Types'
        unique_together = ['name', 'account']


class NotificationTiming(models.Model):
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name='timings')
    timing = models.IntegerField(help_text='Minutes')
    minimum_interest = models.IntegerField(default=0)
    degradation_to_disinterest = models.IntegerField(
        default=0, help_text='0 - 100 %')

    index = models.SmallIntegerField(default=0)

    def __str__(self):
        return (
            f"{self.notification} - {self.timing} minutes : "
            f"min {self.minimum_interest}"
        )

    class Meta:
        verbose_name = 'Notification Timing'
        verbose_name_plural = 'Notification Timings'
