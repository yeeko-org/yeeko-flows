
import json

from django.core.files.base import ContentFile
from pydantic import field_serializer
from typing import Any, Optional

from infrastructure.talk.models import BuiltReply, Interaction

from yeeko_abc_message_models.request import message_model


class InteractionMessage(message_model.MessageBase):
    interaction: Optional[Interaction] = None

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        original_dump = super().model_dump(*args, **kwargs)
        if self.interaction:
            original_dump["interaction"] = str(self.interaction)
        return original_dump

    def record_interaction(self, api_record, member_account, raw_data_in):
        self.interaction = Interaction.objects.create(
            mid=self.message_id,
            interaction_type_id="default",
            member_account=member_account,
            timestamp=self.timestamp,
            api_record_out=api_record,  # salida del servidor
            raw_data_in=raw_data_in,
            raw_data=json.loads(self.model_dump_json()),
        )

    @field_serializer('interaction')
    def serialize_dt(self, interaction: Interaction | None, _info):
        if isinstance(interaction, Interaction):
            return interaction.mid
        return interaction


class TextMessage(message_model.TextMessage, InteractionMessage):
    def record_interaction(self, api_record, member_account):
        return super().record_interaction(api_record, member_account, self.text)


class InteractiveMessage(message_model.InteractiveMessage, InteractionMessage):

    built_reply: Optional[BuiltReply] = None

    def get_built_reply(self):
        try:
            self.built_reply = BuiltReply.objects.get(uuid=self.payload)
        except BuiltReply.DoesNotExist:
            self.built_reply = None

    def record_interaction(self, api_record, member_account):
        return super().record_interaction(api_record, member_account, self.payload)


class EventMessage(message_model.EventMessage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _ = self.interaction

        """
        se puede generar el evento desde aqui, pero revisar si no se calcularan algunas otras acciones
        """

    @property
    def interaction(self):
        if not hasattr(self, "_interaction"):
            try:
                self._interaction = Interaction.objects\
                    .get(mid=self.message_id)
            except Interaction.DoesNotExist:
                self._interaction = None
        return self._interaction


class MediaMessage(message_model.MediaMessage, InteractionMessage):

    def save_content(self):
        if not self.interaction:
            return
        if not self.origin_content:
            return
        if not self.origin_name:
            self.origin_name = f"{self.message_id}.{self.mime_type.split('/')[1]}"

        file = ContentFile(self.origin_content, name=self.origin_name)

        self.interaction.media_in_type = self.media_type
        self.interaction.media_in.save(self.origin_name, file, save=True)

    def record_interaction(self, api_record, member_account):
        _record_interaction = super()\
            .record_interaction(
                api_record, member_account,
                f"{self.media_type}: {self.caption}"
                if self.caption else self.media_type
        )

        self.save_content()

        return _record_interaction
