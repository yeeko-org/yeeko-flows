
import time
from typing import Optional

from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import BuiltReply, Interaction
from pydantic import BaseModel


class MessageBase(BaseModel):
    message_id: str
    timestamp: int
    api_request: Optional[ApiRecord] = None
    context_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def valid_time_interval(self, is_status=False, raise_exception=True):
        max_time = 60000 if is_status else 30000
        self.datetime = self.timestamp
        timestamp_server = int(time.time())
        long_time_interval = self.timestamp > timestamp_server + max_time

        if long_time_interval and raise_exception:
            raise Exception("YA TE PASASTE, ES MUCHO TIEMPO")
        return long_time_interval


class TextMessage(MessageBase):
    text: str


class InteractiveMessage(MessageBase):
    payload: str
    title: Optional[str]
    built_reply: Optional[BuiltReply] = None

    def get_built_reply(self):
        try:
            self.built_reply = BuiltReply.objects.get(uuid=self.payload)
        except BuiltReply.DoesNotExist:
            self.built_reply = None


class EventMessage(MessageBase):
    status: str
    emoji: Optional[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interaction = Interaction.objects.get(mid=self.message_id)

        """
        se puede generar el evento desde aqui, pero revisar si no se calcularan algunas otras acciones
        """

    @property
    def interaction(self):
        if not hasattr(self, "_interaction"):
            self._interaction = Interaction.objects.get(mid=self.message_id)
        return self._interaction
