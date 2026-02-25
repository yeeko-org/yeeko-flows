from typing import List

from services.request.record import RecordRequestAbc
from services.request.message_model import MediaMessage

from yeeko_abc_message_models.messenger import request as m_request


class RecordMessengerRequest(RecordRequestAbc):
    def __init__(self, request: m_request.MessengerRequest) -> None:
        super().__init__(request, platform_name="messenger")

    def get_media_content(self, message: MediaMessage, token: str):
        if not message.multimedia:
            return
        for multimedia in message.multimedia:
            multimedia.media_content = m_request.get_file_content(
                multimedia.media_url, token
            )

    def mark_as_read(self, messages_ids: List[str], pid: str, token: str):
        for message_id in messages_ids:
            m_request.set_sender_action(message_id, pid, token)
