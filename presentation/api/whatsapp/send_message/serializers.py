from rest_framework import serializers

from infrastructure.place.models import Account


class MessageBasicSerializer(serializers.Serializer):
    phone_to = serializers.CharField()
    account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(), write_only=True)
    header = serializers.CharField(required=False, allow_null=True)
    body = serializers.CharField(required=False, allow_null=True)
    footer = serializers.CharField(required=False, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)
    file_type = serializers.CharField(required=False, allow_null=True)
