import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

from utilities.factory_util import safe_pydict


class UserManagerFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    # This is a workaround for the primary key
    username = factory.Faker('uuid4')
    email = factory.Faker('email')
    password = factory.Faker('password')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    # Faker('phone_number') puede pasar de 20 caracteres y rompe el campo
    # User.phone (max_length=20) de forma aleatoria. Lo acotamos.
    phone = factory.Faker('numerify', text='+52##########')
    other_data = safe_pydict()
    gender = factory.Faker('random_element', elements=['Male', 'Female'])
    profile_image = factory.Faker('image_url')


class UserFactory(UserManagerFactory):
    class Meta:
        model = get_user_model()

    is_staff = False
    is_superuser = False
    is_active = True
