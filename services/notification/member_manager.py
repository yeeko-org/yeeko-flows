from collections import defaultdict
from typing import Dict, List

from django.db.models import Q

from infrastructure.assign.models.condition_rule import ConditionRule
from infrastructure.member.models import MemberAccount
from infrastructure.notification.models import Notification
from infrastructure.place.models import Account
from infrastructure.talk.models import NotificationMember
from infrastructure.talk.models.models import Interaction
from infrastructure.xtra.models import Extra


class NotificationManager:
    @classmethod
    def get_notification(
            cls, name: str, account: Account | None,
            raise_exeption: bool = False
    ) -> Notification | None:
        try:
            notification = Notification.objects\
                .get(name=name, account=account)
        except Notification.DoesNotExist:
            notification = None

        if account and not notification:
            # search the global notification
            try:
                notification = Notification.objects.get(
                    name=name, account=None)
            except Notification.DoesNotExist:
                pass

        if not notification and raise_exeption:
            raise Exception(
                f"Notification {name} not found for account {account}")

        return notification

    @classmethod
    def add_notification(
            cls, name: str | Notification, member_account: MemberAccount,
            last_interaction_out: Interaction | None = None,
            **kwargs
    ):
        if isinstance(name, str):
            notification = cls.get_notification(name, member_account.account)
            if not notification:
                return
        else:
            notification = name

        notification_member, _ = NotificationMember.objects.get_or_create(
            notification=notification,
            member_account=member_account,
        )
        notification_member.set_init_controler(last_interaction_out)

        if kwargs:
            notification_member.set_parameters(kwargs)

        notification_member.save()

    @classmethod
    def add_notifications_by_extra(
            cls, extra: Extra, member_account: MemberAccount,
            platform: str = ""
    ):

        condition_rule_query = ConditionRule.objects\
            .filter(notification__isnull=False)\
            .filter(Q(extra=extra) | Q(circles=extra))\
            .order_by("notification").distinct()

        notifications: Dict[Notification, List[ConditionRule]] = \
            defaultdict(list)

        for condition_rule in condition_rule_query:
            if not condition_rule.notification:
                continue
            notifications[condition_rule.notification].append(condition_rule)

        for notification in notifications:
            # There can only be notification if it comes from a condition_rule
            condition_rules = notifications[notification]

            all_conditions = []
            any_conditions = []

            for condition_rule in condition_rules:
                condition_evalue = condition_rule\
                    .evalue(member_account.member, platform)

                if condition_rule.match_all_rules:
                    all_conditions.append(condition_evalue)
                else:
                    any_conditions.append(condition_evalue)

            if not any_conditions and all(all_conditions):
                cls.add_notification(notification, member_account)

            elif any(any_conditions) and all(all_conditions):
                cls.add_notification(notification, member_account)

    @classmethod
    def add_notifications_by_condition_rule(
        cls, condition_rule: ConditionRule, platform_name: str = ""
    ):
        extra = condition_rule.extra

        if not extra:
            return

        members_query = MemberAccount.objects.filter(
            extra_values__extra=extra
        ).distinct()

        for member_account in members_query:
            NotificationManager.add_notifications_by_extra(
                extra, member_account, platform=platform_name
            )
