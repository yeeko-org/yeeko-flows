import json
from interface.whatsapp.account_template import AccountTemplate


class AccountTemplateFile(AccountTemplate):

    def get_templates(self) -> dict:
        with open('interface/whatsapp/ejemplos_template.json', encoding='utf-8') as file:
            templates = json.load(file)
            return templates
