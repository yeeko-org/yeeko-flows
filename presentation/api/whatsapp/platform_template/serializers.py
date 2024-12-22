from rest_framework import serializers


class MessageTemplateSerializer(serializers.Serializer):
    phone_to = serializers.CharField()
    account_id = serializers.CharField()
    template_id = serializers.CharField(required=False, allow_blank=True)
    piece_id = serializers.CharField(required=False, allow_blank=True)
    marked_values = serializers.DictField(required=False)
