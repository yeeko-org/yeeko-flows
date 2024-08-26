from django.test import TestCase

from infrastructure.member.factories import (
    RoleFactory, StatusAttendanceFactory, MemberFactory, MemberAccountFactory,
    ChronoFactory, AuthConfigFactory, InviteExtensionFactory
)
from infrastructure.member.models import (
    Role, StatusAttendance, Member, MemberAccount, Chrono, AuthConfig,
    InviteExtension
)


class TestRoleModel(TestCase):
    def test_role_creation(self):
        role = RoleFactory()
        self.assertIsInstance(role, Role)


class TestStatusAttendanceModel(TestCase):
    def test_status_attendance_creation(self):
        status_attendance = StatusAttendanceFactory()
        self.assertIsInstance(status_attendance, StatusAttendance)


class TestMemberModel(TestCase):
    def test_member_creation(self):
        member = MemberFactory()
        self.assertIsInstance(member, Member)


class TestMemberAccountModel(TestCase):
    def test_member_account_creation(self):
        member_account = MemberAccountFactory()
        self.assertIsInstance(member_account, MemberAccount)


class TestChronoModel(TestCase):
    def test_chrono_creation(self):
        chrono = ChronoFactory()
        self.assertIsInstance(chrono, Chrono)


class TestAuthConfigModel(TestCase):
    def test_auth_config_creation(self):
        auth_config = AuthConfigFactory()
        self.assertIsInstance(auth_config, AuthConfig)


class TestInviteExtensionModel(TestCase):
    def test_invite_extension_creation(self):
        invite_extension = InviteExtensionFactory()
        self.assertIsInstance(invite_extension, InviteExtension)
