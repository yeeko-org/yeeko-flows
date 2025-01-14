from typing import Dict, List, Optional, Type

from django.conf import settings
from django.utils import timezone

from infrastructure.box.models import Destination
from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import NotificationMember
from infrastructure.talk.models.models import Interaction
from services.processor.base_mixin import DestinationProcessorMixin
from services.processor.destination_rules import (
    EndDestinationNotFound, destination_find)
from services.response.abstract import ResponseAbc

NOTIFICATION_LAPSE_MINUTES = getattr(
    settings, 'NOTIFICATION_LAPSE_MINUTES', 15)

PLATFORM_NAME_FOR_NOTIFICATION = getattr(
    settings, 'PLATFORM_NAME_FOR_NOTIFICATION', "notification")

INTERACTION_TYPE_NAME_FOR_NOTIFICATION = getattr(
    settings, 'INTERACTION_TYPE_NAME_FOR_NOTIFICATION', "notification")


class NotificationProcesor(DestinationProcessorMixin):
    notification_member: NotificationMember
    response: ResponseAbc
    destination: Optional[Destination] = None

    def __init__(
            self, notification_member: NotificationMember,
            response: ResponseAbc,
            parameters: dict = None
    ):
        if parameters is None:
            self.parameters = {}
        else:
            self.parameters = parameters.copy()
        self.notification_member = notification_member
        self.response = response

    def get_destination(self):
        self.destination = destination_find(
            self.notification_member.notification.get_destinations(),
            self.notification_member.member_account.member,
            self.response.platform_name,
            raise_exception=True
        )


class SlopsCalculation:
    account: Account
    notifications_by_member: Dict[MemberAccount, List[NotificationMember]]
    platform_name: str
    response_class: Type[ResponseAbc]
    errors: List[Dict[str, str]] = []

    request_data: dict = {}

    def __init__(
            self, account: Account, response_class: Type[ResponseAbc],
            platform_name: str = "", request_data: dict = None
    ):
        if request_data is None:
            request_data = {}
        self.account = account
        self.platform_name = platform_name or self.platform_name
        self.response_class = response_class
        self.request_data = request_data

        self.calculate_slope()

    def calculate_slope(self):
        # all pending notifications
        # order by minimum_interest lest value
        simultaneous_slope_notifications_limit = getattr(
            settings, 'SIMULTANEOUS_SLOPE_NOTIFICATIONS_LIMIT', 200
        )
        pile_query = NotificationMember.objects\
            .filter(next_at__lte=timezone.now())\
            .select_related("notification", "member_account")\
            .order_by("actual_timing__minimum_interest", "created_at")

        self.notifications_by_member = {}
        count_notifications = 0
        for pile in pile_query:
            if pile.member_account not in self.notifications_by_member:
                self.notifications_by_member[pile.member_account] = []

            self.notifications_by_member[pile.member_account].append(pile)

            # por notificación exitosa, no va aquí
            count_notifications += 1
            if count_notifications > simultaneous_slope_notifications_limit:
                break

    def process_notifications(self):
        for member_account, notifications in self.notifications_by_member.items():
            self.process_member(notifications, member_account)

    def process_member(
            self, notifications_member: List[NotificationMember],
            member: MemberAccount
    ):

        last_interaction_out = Interaction.objects.filter(
            is_incoming=False, member_account=member
        ).order_by("-created_at").first()
        if last_interaction_out:
            elapsed_time = timezone.now() - last_interaction_out.created
            elapsed_minutes = int(elapsed_time.total_seconds() / 60)
        else:
            elapsed_minutes = 0  # puede pasar?

        api_record_in = ApiRecord.objects.create(
            platform_id=PLATFORM_NAME_FOR_NOTIFICATION,
            interaction_type_id=INTERACTION_TYPE_NAME_FOR_NOTIFICATION,
            body=self.request_data.copy(),
        )

        response = self.response_class(
            sender=member, platform_name=self.platform_name,
            api_record_in=api_record_in)

        while notifications_member:
            notification_member = notifications_member.pop(0)

            out_min_time = notification_member.notification\
                .min_gap_last_interaction_out
            if out_min_time > elapsed_minutes:
                # check if the minimum time has passed
                continue

            parameters = notification_member.parameters.get_value()
            if not isinstance(parameters, dict):
                parameters = {}

            processor = NotificationProcesor(
                notification_member=notification_member,
                response=response,
                parameters=parameters
            )
            try:
                processor.process_destination()
                response.trigger = None
                response.set_trigger(notification_member.notification)
                break
            except EndDestinationNotFound:
                notification_member.set_next_controler()
            except Exception as e:
                notification_member.next_at_not_chosen()
                response.add_error(
                    {"method": "SlopsCalculation.process_member"}, e=e)

        for notification_member in notifications_member:
            notification_member.next_at_not_chosen()

        response.send_messages()
