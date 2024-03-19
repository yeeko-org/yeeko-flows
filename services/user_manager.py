from typing import Optional

from django.contrib.auth.hashers import make_password
from django.conf import settings

from infrastructure.users.models import User
from infrastructure.member.models import Member, MemberAccount, Role, StatusAttendance
from infrastructure.place.models import Account


class MemberAccountManager:
    def __init__(
        self,
        account: Account,
        sender_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        user_field_filter: Optional[str] = None,
        **kwargs
    ):
        self.account = account
        self.sender_id = sender_id
        self.name = name
        self.email = email
        self.phone = phone
        self.user_field_filter = user_field_filter

        self.kwargs = kwargs

        self.is_new_sender = False

    def get_member_account(self):
        """
        Agregar campos adicionales de user:
        is_staff
        """

        try:
            return MemberAccount.objects.get(
                uid=self.sender_id, account=self.account
            )
        except MemberAccount.DoesNotExist:
            return self.create_member_account()

    def create_member_account(self):
        try:
            user = self.get_user()
        except User.DoesNotExist:
            user = self.create_user()
        member = self.get_or_create_member(user)
        self.is_new_sender = True
        status_default, _ = StatusAttendance.objects\
            .get_or_create(name="chatbot")

        return MemberAccount.objects.create(
            member=member, account=self.account, uid=self.sender_id,
            status=status_default, ** self.kwargs)

    def get_user(self):
        if self.user_field_filter:
            return User.objects.get(
                **{self.user_field_filter: self.sender_id})
        return User.objects.get(username=self.sender_id)

    def create_user(self):
        private_hash = getattr(settings, "CREATE_USER_PRIVATE_HASH")
        user = User.objects.create(
            username=self.sender_id,
            first_name=self.name or self.sender_id,
            last_name="",
            email=self.email or "",
            phone=self.phone,
            password=make_password(self.sender_id + private_hash),
        )

        return user

    def get_or_create_member(self, user: User):
        member = Member.objects.filter(
            user=user, space=self.account.space).first()
        if member:
            return member
        default_role, _ = Role.objects.get_or_create(name="normal")
        return Member.objects.create(
            user=user, space=self.account.space, role=default_role
        )
