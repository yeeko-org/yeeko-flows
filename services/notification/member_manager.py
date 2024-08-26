from infrastructure.member.models import MemberAccount
from infrastructure.notification.models import Notification
from infrastructure.place.models import Account
from infrastructure.talk.models import NotificationMember


class NotificationManager:

    def get_notification(
            self, name: str, account: Account | None, raise_exeption: bool = False
    ) -> Notification | None:
        try:
            notification = Notification.objects.get(name=name, account=account)
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

    def add_notification(
            self, name: str, member_account: MemberAccount, **kwargs
    ):
        notification = self.get_notification(name, member_account.account)
        if not notification:
            return

        notification_member, _ = NotificationMember.objects.get_or_create(
            notification=notification,
            member_account=member_account,
            successful=None
        )
        notification_member.set_init_controler()

        if kwargs:
            notification_member.set_parameters(kwargs)

        notification_member.save()
