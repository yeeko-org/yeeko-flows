from django.conf import settings
import requests
from infrastructure.box.models import Reply
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import BuiltReply
from services.message_templates.template_out import MessageTemplateOutAbstract
from services.response.models import Button, Header, ReplyMessage
from utilities.standard_phone import standard_mx_phone

FACEBOOK_API_VERSION = getattr(settings, 'FACEBOOK_API_VERSION', 'v19.0')


PLATFORM_NAME_FOR_DASHBOARD = getattr(
    settings, 'PLATFORM_NAME_FOR_DASHBOARD', "dashboard")


class MessageTemplate(MessageTemplateOutAbstract):

    def make_message(self) -> dict:

        self.message_display = ReplyMessage(body="")
        components = []

        header = self.get_header()
        if header:
            components.append(header)

        body = self.get_body()
        if body:
            components.append(body)

        footer = self.get_footer()
        if footer:
            components.append(footer)

        buttons = self.get_buttons()
        if buttons:
            components.extend(buttons)

        return {
            "name": self.template.name,
            "language": {
                "code": self.template.language
            },
            "components": components
        }

    def get_component_base(self, type_component) -> dict | None:
        if not self.template_parameters:
            # no parameters
            return

        parameters_data = []
        for parameter in self.template_parameters:
            if parameter.component_type.lower() == type_component.lower():

                if parameter.extra:
                    value = self.marked_values.get(
                        parameter.extra.name) or parameter.default_value
                else:
                    value = parameter.default_value
                parameters_data.append({
                    "type": "text",
                    "text": value or ""
                })

        if not parameters_data:
            # no parameters for the component
            return

        return {
            "type": type_component,
            "parameters": parameters_data
        }

    def get_header(self) -> dict | None:

        if not self.fragment.header and not self.fragment.media_type:
            return

        if not self.fragment.media_type:
            self.message_display.header = self.fragment.header

            return self.get_component_base("HEADER")

        media_type = self.fragment.media_type
        if self.fragment.file:
            link = self.fragment.file.url
        else:
            link = self.fragment.media_url

        if not link:
            raise ValueError("Media link is required")

        self.message_display.header = Header(type=media_type, value=link)

        return {
            "type": "HEADER",
            "parameters": [
                {
                    "type": media_type,
                    media_type: {
                        "link": self.fragment.file.url
                        if self.fragment.file else self.fragment.media_url
                    }
                }
            ]
        }

    def get_body(self) -> dict | None:
        if not self.fragment.body:
            return

        self.message_display.body = self.fragment.body

        return self.get_component_base("BODY")

    def get_footer(self) -> dict | None:
        if not self.fragment.footer:
            return

        self.message_display.footer = self.fragment.footer

        return self.get_component_base("FOOTER")

    def get_buttons(self) -> list:
        components = []
        self.reply_uuids = []
        replay_query = Reply.objects.filter(
            fragment=self.fragment,
            reply_type__in=["quick_reply", "url"]).order_by("order")
        reply_index = 0
        for reply in replay_query:
            component = {
                "type": "button",
                "sub_type": reply.reply_type,
                "index": reply_index,
            }

            if reply.reply_type == "quick_reply":

                built_reply = BuiltReply.objects.create(
                    reply=reply,
                    is_for_reply=True,
                )
                uuid = str(built_reply.uuid)
                self.reply_uuids.append(uuid)

                component["parameters"] = [{
                    "type": "payload",
                    "payload": uuid,
                }]

                self.message_display.buttons.append(
                    Button(
                        title=reply.title or "",
                        payload=uuid,
                        description=reply.reply_type
                    )
                )

            else:
                component["parameters"] = [{
                    "type": "text",
                    "text": reply.large_title
                }]

                self.message_display.buttons.append(
                    Button(
                        title=reply.title or "",
                        payload=reply.large_title or "",
                        description=reply.reply_type
                    )
                )

            reply_index += 1
            components.append(component)

        return components

    def send_message(self, phone_to: str | None) -> str | None:
        self.api_record = None
        if self.member_account:
            # if member account already set has higher priority
            self.phone_to = self.member_account.uid
        elif phone_to:
            try:
                self.phone_to = standard_mx_phone(phone_to)
            except Exception as e:
                raise ValueError(f"Phone {phone_to} error: {e}")
        else:
            raise ValueError("Send phone is required")

        base_url = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'
        url = f"{base_url}/{self.account.pid}/messages"
        headers = {
            "Authorization": f"Bearer {self.account.token}",
            "Content-Type": "application/json",
        }
        template_message_data = self.make_message()
        message_data = {
            "messaging_product": "whatsapp",
            "to": self.phone_to,
            "type": "template",
            "template": template_message_data,
        }
        response = requests.post(url, headers=headers, json=message_data)
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"body": response.text}

        self.api_record = ApiRecord.objects.create(
            platform_id=PLATFORM_NAME_FOR_DASHBOARD,
            body=message_data,
            interaction_type_id="default",
            is_incoming=False,
            response_status=response.status_code,
            response_body=response_body
        )

        mid = None
        messages = response_body.get("messages")
        if messages:
            try:
                mid = messages[0].get("id")  # type: ignore
            except Exception:
                pass
        if mid:
            self.record_interaction(mid)

        return mid
