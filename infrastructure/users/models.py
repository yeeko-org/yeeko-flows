from django.db import models
from django.db.models import JSONField
from django.contrib.auth.models import (
    AbstractUser, PermissionsMixin, BaseUserManager
)

from django.dispatch import receiver
from django.db.models.signals import post_save


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('El usuario debe tener un email válido')
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)

        return self.create_user(email, password, **kwargs)


class User(AbstractUser, PermissionsMixin):
    phone = models.CharField(max_length=20, blank=True, null=True)
    other_data = JSONField(blank=True, null=True)
    gender = models.CharField(max_length=300, blank=True, null=True)
    profile_image = models.ImageField(
        blank=True, null=True,
    )

    objects = UserManager() # type: ignore

    # TODO Ricardo: Revisar si se deja por serializador o por diccionario

    def get_basic_data(self):
        from rest_framework import serializers
        class BasicSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = [
                    'username', 'email', 'first_name', 'last_name',
                    'phone', "gender"
                ]
        serializer = BasicSerializer(self)
        return serializer.data

        return {
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'gender': self.gender,
        }

    class Meta:
        db_table = 'auth_user'


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    from rest_framework.authtoken.models import Token
    if created:
        _ = Token.objects.get_or_create(user=instance)
