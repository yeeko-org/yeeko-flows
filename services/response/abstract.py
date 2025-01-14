import json
import traceback

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Callable, List, Optional, Union

from infrastructure.box.models import PlatformTemplate, Written
from infrastructure.member.models import MemberAccount
from infrastructure.notification.models import Notification
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import BuiltReply, Interaction, Trigger
from infrastructure.tool.models import Behavior
from infrastructure.xtra.models import Extra
from services.notification.member_manager import NotificationManager
from services.response.models import MediaMessage, Message, SectionsMessage, ReplyMessage
from utilities.parameters import replace_parameter


def exception_handler(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.add_error({"method": func.__name__, }, e=e)

    return wrapper


def _rep_text(text: str, sender: MemberAccount, default: str = "") -> str:
    return replace_parameter(
        sender.member.get_extra_values_data(),
        text,
        default=default
    )


class ResponseAbc(ABC, BaseModel):
    sender: MemberAccount
    api_record_in: ApiRecord | None = None
    message_list: List[dict] = []
    platform_name: str
    trigger: Trigger | None = None

    errors: List[dict] = []

    class Config:
        arbitrary_types_allowed = True

    @exception_handler
    def message_text(self, message: str, fragment_id: Optional[int] = None):
        message = _rep_text(message, self.sender)
        message_data = self.text_to_data(message, fragment_id=fragment_id)

        message_data["_standard_message"] = json.loads(
            Message(body=message).model_dump_json())
        self.message_list.append(message_data)

    # @exception_handler
    def message_multimedia(
        self, media_type: str, url_media: str = "", media_id: str = "", caption: str = "",
        fragment_id: Optional[int] = None
    ):
        caption = _rep_text(caption, self.sender)
        message_data = self.multimedia_to_data(
            url_media, media_id, media_type, caption, fragment_id=fragment_id)
        message_data["_standard_message"] = json.loads(MediaMessage(
            caption=caption, id=media_id, link=url_media).model_dump_json())
        self.message_list.append(message_data)

    @exception_handler
    def message_few_buttons(self, message: ReplyMessage):
        message.replace_text(self.sender.member.get_extra_values_data())

        message_data = self.few_buttons_to_data(message)
        message_data["_standard_message"] = json.loads(
            message.model_dump_json())
        self.message_list.append(message_data)

    @exception_handler
    def message_many_buttons(self, message: ReplyMessage):
        message.replace_text(self.sender.member.get_extra_values_data())

        message_data = self.many_buttons_to_data(message)
        message_data["_standard_message"] = json.loads(
            message.model_dump_json())
        self.message_list.append(message_data)

    @exception_handler
    def message_sections(self, message: SectionsMessage):
        message.replace_text(self.sender.member.get_extra_values_data())

        message_data = self.sections_to_data(message)
        message_data["_standard_message"] = json.loads(
            message.model_dump_json())
        self.message_list.append(message_data)

    def send_messages(self):
        for message in self.message_list:
            uuid_list = message.pop("uuid_list", [])
            fragment_id = message.get("_fragment_id", None)
            standard_message = message.get("_standard_message", None)
            print(type(standard_message))
            try:
                api_record_out = self.send_message(message)
            except Exception as e:

                self.add_error(
                    {"method": "send_message",  "message": message}, e=e
                )
                continue
            try:
                self.save_interaction(
                    api_record_out, message, uuid_list, fragment_id, standard_message)
            except Exception as e:
                self.add_error(
                    {"method": "save_interaction"}, e=e
                )

    @abstractmethod
    def text_to_data(
        self, message: str, fragment_id: Optional[int] = None
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def multimedia_to_data(
        self, url_media: str, media_id: str, media_type: str, caption: str,
        fragment_id: Optional[int] = None
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def few_buttons_to_data(self, message: ReplyMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def many_buttons_to_data(self, message: ReplyMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sections_to_data(self, message: SectionsMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self, message_data: dict
    ) -> ApiRecord:
        raise NotImplementedError

    @abstractmethod
    def get_mid(self, body: Optional[dict]) -> Optional[str]:
        raise NotImplementedError

    def save_interaction(
        self, api_record_out: ApiRecord, message_data: dict,
        uuid_list: List[str] = [], fragment_id: Optional[int] = None,
        standard_message: Optional[dict] = None
    ) -> None:

        if api_record_out.response_status != 200:
            # a quien oertenece el error?
            self.add_errors(
                [
                    {
                        "error": "Error en la respuesta de salida",
                        "method": "save_interaction",
                        "status": api_record_out.response_status,
                        "body": api_record_out.response_body
                    }
                ]
            )
            return

        mid = self.get_mid(api_record_out.response_body)
        if not mid:
            self.add_errors(
                [
                    {
                        "error": "No se pudo obtener el mid",
                        "method": "save_interaction",
                        "status": api_record_out.response_status,
                        "body": api_record_out.response_body
                    }
                ]
            )
            return

        interaction = Interaction.objects.create(
            mid=mid,
            interaction_type_id="default",
            is_incoming=False,
            member_account=self.sender,
            api_record_out=api_record_out,
            raw_data_in=json.dumps(message_data),
            fragment_id=fragment_id,
            raw_data=standard_message,
            trigger=self.trigger
        )
        if self.api_record_in:
            interaction.api_record_in.add(self.api_record_in)

        BuiltReply.objects.filter(uuid__in=uuid_list).update(
            interaction=interaction)

    def set_trigger(
            self,
            trigger_origin: Union[
                Behavior, Interaction, BuiltReply, Written, PlatformTemplate,
                Notification, None
            ],
            is_direct: bool = False,
            interaction_in: Interaction | None = None
    ) -> None:
        if self.trigger:
            return
        if not trigger_origin:
            return

        trigger = Trigger()
        trigger.is_direct = is_direct
        trigger.interaction_reply = interaction_in  # type: ignore

        if isinstance(trigger_origin, Behavior):
            trigger.behavior = trigger_origin
        elif isinstance(trigger_origin, BuiltReply):
            trigger.built_reply = trigger_origin  # type: ignore
        elif isinstance(trigger_origin, Written):
            trigger.written = trigger_origin
        elif isinstance(trigger_origin, PlatformTemplate):
            trigger.template = trigger_origin
        elif isinstance(trigger_origin, Notification):
            trigger.notification = trigger_origin

        trigger.save()
        self.trigger = trigger

    def add_error(self, error: dict, e: Optional[BaseException] = None):
        if self.api_record_in:
            self.api_record_in.add_error(error, e=e)
            return

        if e:
            error["error"] = str(e)
            error["traceback"] = traceback.format_exc()
        self.errors.append(error)

    def add_errors(self, errors: list, e: Optional[BaseException] = None) -> None:
        if self.api_record_in:
            self.api_record_in.add_errors(errors, e=e)

        else:
            self.errors.extend(errors)

    def add_extra_value(
            self, extra: Extra,  value: str | None = None,
            interaction: Interaction | None = None, origin: str = "unknown",
            list_by=None
    ):
        extra_value = self.sender.member.add_extra_value(
            extra,  value, interaction, origin, list_by
        )

        if not extra_value:
            self.add_error(
                {"method": "add_extra_value", "extra": extra.pk, "value": value}
            )
            return

        NotificationManager.add_notifications_by_extra(
            extra, self.sender, platform=self.platform_name
        )
