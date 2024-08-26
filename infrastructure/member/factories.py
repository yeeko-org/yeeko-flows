import factory
from factory.django import DjangoModelFactory

from infrastructure.member.models import (
    Role, StatusAttendance, Member, MemberAccount, Chrono, AuthConfig,
    InviteExtension
)
from infrastructure.place.factories import SpaceFactory, AccountFactory
from infrastructure.service.factories import PlatformFactory
from infrastructure.users.factories import UserFactory

from utilities.factory_util import optional_sub_factory, safe_pydict


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role

    name = factory.Faker('uuid4')  # This is a workaround for the unique
    public_name = factory.Faker('word')
    has_dashboard_access = factory.Faker('boolean')
    can_moderate = factory.Faker('boolean')
    can_admin = factory.Faker('boolean')
    can_edit = factory.Faker('boolean')
    is_tester = factory.Faker('boolean')
    is_default = factory.Faker('boolean')
    order = factory.Faker('random_int', min=1, max=100)


class StatusAttendanceFactory(DjangoModelFactory):
    class Meta:
        model = StatusAttendance

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('sentence')
    color = factory.Faker('hex_color')
    icon = factory.Faker('word')
    show_in_tracking = factory.Faker('boolean')
    text_response = factory.Faker('boolean')
    payload_response = factory.Faker('boolean')


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = Member

    space = factory.SubFactory(SpaceFactory)
    user = factory.SubFactory(UserFactory)
    active = factory.Faker('boolean')
    role = factory.SubFactory(RoleFactory)
    created = factory.Faker('date_time_this_decade')
    subscribed = factory.Faker('boolean')
    deleted = factory.Faker('boolean')


class MemberAccountFactory(DjangoModelFactory):
    class Meta:
        model = MemberAccount

    member = factory.SubFactory(MemberFactory)
    account = factory.SubFactory(AccountFactory)
    uid = factory.Faker('uuid4')
    token = factory.Faker('sha256')
    config = safe_pydict()
    last_interaction = factory.Faker('date_time_this_year')
    status = optional_sub_factory(StatusAttendanceFactory)


class ChronoFactory(DjangoModelFactory):
    class Meta:
        model = Chrono

    member_account = factory.SubFactory(MemberAccountFactory)
    checking_lapse = factory.Faker('random_int', min=1, max=100)
    last_notify = factory.Faker('date_time_this_year')
    checking_date = factory.Faker('date_time_this_year')
    interest_degree = factory.Faker('random_int', min=1, max=100)
    interest_current = factory.Faker('random_int', min=1, max=100)


class AuthConfigFactory(DjangoModelFactory):
    class Meta:
        model = AuthConfig

    platform = factory.SubFactory(PlatformFactory)
    user = factory.SubFactory(UserFactory)
    uid = factory.Faker('uuid4')
    token = factory.Faker('sha256')
    config = safe_pydict()


class InviteExtensionFactory(DjangoModelFactory):
    class Meta:
        model = InviteExtension

    member = optional_sub_factory(MemberFactory)
    space = optional_sub_factory(SpaceFactory)
    key = factory.Faker('word')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    response = factory.Faker('text')
    date_invitation = factory.Faker('date_time_this_year')
    date_accepted = factory.Faker('date_time_this_year')
    inviter_user = factory.SubFactory(UserFactory)
    viewed = factory.Faker('date_time_this_year')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    gender = factory.Faker('random_element', elements=['Male', 'Female'])
    other_data = safe_pydict()
    verified = factory.Faker('boolean')
    role = factory.SubFactory(RoleFactory)
