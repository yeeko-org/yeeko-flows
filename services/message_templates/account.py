from abc import ABC, abstractmethod
from infrastructure.box.models import Fragment, Piece, Reply, PlatformTemplate
from infrastructure.flow.models import Crate, CrateType, Flow
from infrastructure.place.models import Account


class AccountTemplateAbstact(ABC):
    account: Account
    headers: dict
    api_url: str

    def __init__(self, account: Account) -> None:
        self.account = account

    @abstractmethod
    def get_templates(self) -> dict:
        """Get all templates from api platform"""
        raise NotImplementedError

    @abstractmethod
    def create_template(self, template: dict) -> dict:
        """Create a template in api platform for the account"""
        raise NotImplementedError

    @abstractmethod
    def fetch_templates(self):
        """Fetch templates from api platform and save them in the database"""
        raise NotImplementedError

    @abstractmethod
    def get_template_components(self, raw_template: dict) -> dict:
        """
        Get the particular components of the template in standard format

        {
            "header": "Header text",
            "header_format": "TYPE",
            "body": "Body text",
            "footer": "Footer text",
            "buttons": [button_data]
        }
        """
        raise NotImplementedError

    @abstractmethod
    def create_button_reply(self, fragment: Fragment, button: dict):
        """Create a button reply from particular button data"""
        raise NotImplementedError

    def get_crate_template(self) -> Crate:
        crate = Crate.objects.filter(
            name="Templates",
            flow__space=self.account.space
        ).first()

        if not crate:
            crate_type, _ = CrateType.objects.get_or_create(
                name="Templates")
            flow = Flow.objects.get_or_create(
                name="Templates", space=self.account.space)
            crate = Crate.objects.create(
                name="Templates",
                crate_type=crate_type,
                flow=flow,
            )
        return crate

    @property
    def crate_template(self):
        if not hasattr(self, "_crate_template"):
            self._crate_template = self.get_crate_template()
        return self._crate_template

    def create_template_object(
        self,
        raw_template,
        template_id,
        name,
        status,
        category,
        lenguage
    ):

        template, _ = PlatformTemplate.objects.get_or_create(
            account=self.account,
            template_id=template_id
        )
        template.name = name
        template.status = status
        template.category = category
        template.language = lenguage
        template.raw_template = raw_template
        template.save()

        self.template_update_piece(template)
        self.template_update_fragment(template)

    def template_update_piece(self, template: PlatformTemplate):
        if template.piece:
            return
        piece = Piece()
        piece.piece_type = "template"
        piece.crate = self.crate_template
        piece.name = template.name
        piece.description = template.description or template.name
        piece.save()
        template.piece = piece
        template.save()

    def template_update_fragment(self, template: PlatformTemplate):
        components_dict = self.get_template_components(template.raw_template)

        header = components_dict.get('header')
        header_format = components_dict.get('header_format')
        body = components_dict.get('body')
        footer = components_dict.get('footer')
        buttons = components_dict.get('buttons', [])

        fragment = Fragment.objects.filter(piece=template.piece).first()
        if not fragment:
            fragment = Fragment.objects.create(
                piece=template.piece
            )

        fragment.fragment_type = "message"
        fragment.header = header
        fragment.body = body
        fragment.footer = footer
        header_formats = {
            "IMAGE": "image",
            "VIDEO": "video",
            "AUDIO": "audio",
        }
        if header_format:
            fragment.media_type = header_formats.get(header_format)
        fragment.save()

        Reply.objects.filter(fragment=fragment).delete()

        for button in buttons:
            self.create_button_reply(fragment, button)
