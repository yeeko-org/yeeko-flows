from services.request import RequestAbc
from services.request.message_model import MediaMessage

from yeeko_abc_message_models.whatsapp_message import request as w_request


class WhatsAppRequest(RequestAbc, w_request.WhatsAppRequest):
    def __init__(self, raw_data: dict, debug=False) -> None:
        super().__init__(raw_data, debug=debug, platform_name="whatsapp")

    def _record_metadata(self) -> None:
        for input_account in self.input_accounts:
            pid = input_account.account.pid
            token = input_account.account.token
            if not token:
                continue
            for input_sender in input_account.members:
                for message in input_sender.messages:
                    w_request.set_status_read(message.message_id, pid, token)
                    if isinstance(message, MediaMessage):
                        message.origin_content = w_request.get_file_content(
                            message.media_id, token
                        )
