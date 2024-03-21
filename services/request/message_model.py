
import time
from typing import Optional

from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import BuiltReply
from pydantic import BaseModel


class MessageBase(BaseModel):
    message_id: str
    timestamp: int
    api_request: Optional[ApiRecord] = None

    class Config:
        arbitrary_types_allowed = True

    def get_base_info(self, is_status=False):
        max_time = 60000 if is_status else 30000
        self.datetime = self.timestamp
        timestamp_server = int(time.time())
        if self.timestamp > timestamp_server + max_time:
            raise Exception("YA TE PASASTE, ES MUCHO TIEMPO")


class TextMessage(MessageBase):

    text: str
    message_id: str
    timestamp: int


class InteractiveMessage(MessageBase):

    built_reply: Optional[BuiltReply]
    message_id: str
    payload: str
    timestamp: int
    text: Optional[str]
    title: Optional[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_built_reply()

    def get_built_reply(self):
        if self.payload.isdigit():
            try:
                self.built_reply = BuiltReply.objects.get(uuid=self.payload)
            except BuiltReply.DoesNotExist:
                self.built_reply = None


class EventMessage(MessageBase):

    message_id: Optional[str]
    status: str
    timestamp: int
