from pydantic import BaseModel
from typing import List, Optional


class Button(BaseModel):
    title: str
    payload: str
    description: Optional[str] = None


class SectionHeader(BaseModel):
    title: str


class Header(BaseModel):
    type: str
    value: str


class Message(BaseModel):
    body: str
    header: Optional[str | Header] = None
    footer: Optional[str] = None
    fragment_id: Optional[int] = None


class ReplyMessage(Message):
    buttons: List[Button | SectionHeader] = []
    button_text: str = "Seleccionar ⏬"

    def get_section(
            self, default_title="Opciones", available_button_space=10
    ) -> List["Section"]:
        sections: List["Section"] = []

        actual_section = None

        for button in self.buttons:
            if isinstance(button, SectionHeader):

                if actual_section and actual_section.buttons:
                    sections.append(actual_section)

                actual_section = Section(title=button.title)
            else:

                if not actual_section:
                    actual_section = Section(title=default_title)

                available_button_space -= 1
                actual_section.buttons.append(button)

            if not available_button_space:
                break

        if actual_section:
            sections.append(actual_section)

        return sections

    def has_sections(self) -> bool:
        return any(isinstance(button, SectionHeader) for button in self.buttons)

    def get_only_buttons(self) -> List[Button]:
        return [button for button in self.buttons if isinstance(button, Button)]


class Section(BaseModel):
    title: str
    buttons: List[Button] = []


class SectionsMessage(Message):
    button_text: str
    sections: List[Section]
    top_element_style: Optional[str] = "compact"
