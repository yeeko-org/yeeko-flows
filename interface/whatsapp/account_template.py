import requests

from django.conf import settings

from infrastructure.box.models import Fragment, Reply
from infrastructure.place.models import Account
from services.message_templates.account import AccountTemplateAbstact

FACEBOOK_API_VERSION = getattr(settings, 'FACEBOOK_API_VERSION', 'v20.0')
FACEBOOK_API_URL = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'


class AccountTemplate(AccountTemplateAbstact):

    def __init__(self, account: Account) -> None:
        super().__init__(account)
        self.headers = {
            "Authorization": f"Bearer {self.account.token}",
            "Content-Type": "application/json",
        }
        self.api_url = f"{FACEBOOK_API_URL}/{self.account.app_id}/message_templates"

    def get_templates(self) -> dict:
        self.response = requests.get(self.api_url, headers=self.headers)
        if self.response.status_code != 200:
            print(self.response.status_code)
            print(self.response.json())
            return {}
        return self.response.json()

    def create_template(self, template: dict) -> dict:
        self.response = requests.post(
            self.api_url, headers=self.headers, json=template)
        return self.response.json()

    def fetch_templates(self):
        templates_response_json = self.get_templates()
        template_data = templates_response_json.get('data', [])

        if not template_data:
            return

        for template in template_data:
            template_id = template.get('id')
            template_name = template.get('name')
            template_status = template.get('status')
            template_category = template.get('category')
            template_lenguage = template.get('lenguage')
            self.create_template_object(
                template,
                template_id,
                template_name,
                template_status,
                template_category,
                template_lenguage
            )

    def get_template_components(self, raw_template: dict) -> dict:
        components_list = raw_template.get('components', [])
        components_dict = {}
        for component in components_list:
            component_type = component.get('type')
            components_dict[component_type] = component

        body = components_dict.get('BODY', {}).get("text")
        footer = components_dict.get('FOOTER', {}).get("text")
        buttons = components_dict.get('BUTTONS', {}).get('buttons', [])

        header_data = components_dict.get('HEADER')
        header_format = None
        header = None
        if header_data:
            header_format = header_data.get('format')
            if header_format == "TEXT":
                header = header_data.get('text')

        return {
            "header": header,
            "header_format": header_format,
            "body": body,
            "footer": footer,
            "buttons": buttons,
        }

    def create_button_reply(self, fragment: Fragment, button: dict):
        button_type = button.get('type', "")
        button_text = button.get('text')
        button_url = button.get('url')

        button_reply = Reply(
            reply_type=button_type.lower(),
            fragment=fragment,
            title=button_text,
        )
        if button_url:
            button_reply.large_title = button_url

        button_reply.save()
