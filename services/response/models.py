from pydantic import BaseModel
from typing import List, Optional


class Button(BaseModel):
    title: str
    payload: str
    description: Optional[str] = None


button = Button()


class Header(BaseModel):
    type: str
    value: str


class Message(BaseModel):
    body: str
    header: Optional[str | Header] = None
    footer: Optional[str] = None


class ReplyMessage(Message):
    buttons: List[Button] = []
    button_text: str = "Seleccionar ⏬"


class Section(BaseModel):
    title: str
    buttons: List[Button] = []


class SectionsMessage(Message):
    button_text: str
    sections: List[Section]
    top_element_style: Optional[str] = "compact"
