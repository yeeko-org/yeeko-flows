from pydantic import BaseModel
from typing import List, Optional

from utilities.parameters import replace_parameter

from yeeko_abc_message_models.response import models as y_models
from yeeko_abc_message_models.response.models import (
    Button, SectionHeader, Header, Section, MediaMessage)


class Message(y_models.Message):
    fragment_id: Optional[int] = None

    def get_context(self):
        return {"fragment_id": self.fragment_id}


class ReplyMessage(Message, y_models.ReplyMessage):
    pass


class SectionsMessage(Message, y_models.SectionsMessage):
    pass
