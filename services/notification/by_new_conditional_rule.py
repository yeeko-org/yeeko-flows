from infrastructure.member.models import MemberAccount
from infrastructure.xtra.models import Extra
from services.notification.member_manager import NotificationManager


class NewConditionalRule:
    @classmethod
    def find_members(cls, extra: Extra, platform_name: str):

        members_query = MemberAccount.objects.filter(
            extra_values__extra=extra
        ).distinct()

        for member_account in members_query:
            NotificationManager.add_notifications_by_extra(
                extra, member_account, platform=platform_name
            )
