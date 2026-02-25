from typing import List

from services.request.record import RecordRequestAbc
from services.request.message_model import MediaMessage

from yeeko_abc_message_models.whatsapp_message import request as w_request
from yeeko_abc_message_models.whatsapp_message.request import WhatsAppRequest as _WhatsAppRequest


class WhatsAppRequest(_WhatsAppRequest):
    """Subclase local que pre-inicializa `_contacts_data` antes de `super().__init__()`
    para corregir el bug de orden de inicialización de la librería."""

    def __init__(self, raw_data: dict, debug=False) -> None:
        self._contacts_data = {}
        super().__init__(raw_data, debug=debug)


class RecordWhatsAppRequest(RecordRequestAbc):
    def __init__(self, request: WhatsAppRequest) -> None:
        super().__init__(request, platform_name="whatsapp")

    def get_media_content(self, message: MediaMessage, token: str):
        message.origin_content = w_request.get_file_content(
            message.media_id, token
        )

    def mark_as_read(
            self, pid: str, token: str,
            messages_ids: List[str] | None = None, uids: List[str] | None = None
    ):
        for message_id in (messages_ids or []):
            w_request.set_status_read(message_id, pid, token)
