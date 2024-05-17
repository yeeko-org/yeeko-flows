import re
from typing import Optional

# from bot_message.models import Message
# from bot_user.models import MsgSend, Answer
from infrastructure.box.models import Piece, Written
from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
# from scripts.common import has_admin
# from proposals.models import Proposal
# from bot_core.models import BotError
# from .DespachadorPayload import DespachadorPayload
# from .OtherModule import languageFilter
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra
from services.processor.behavior_processor import BehaviorProcessor
from services.processor.processor_base import Processor
from services.request import RequestAbc
from services.request.message_model import MessageBase, TextMessage
from services.response import ResponseAbc


class TextMessageProcessor(Processor):
    sender: MemberAccount
    api_request: ApiRecord
    request_message_id: str
    message: TextMessage
    response: ResponseAbc
    written: Optional[Written]
    default_extra: Optional[Extra]

    def __init__(
            self, manager_flow, message: TextMessage, response: ResponseAbc
    ) -> None:
        self.manager_flow = manager_flow
        self.message = message
        self.sender = response.sender

        self.response = response
        self.set_writen_context()

    def set_writen_context(self):
        context_piece = None
        self.context_direct = False
        if self.message.context_id:
            context_piece = Piece.objects.filter(
                fragments__interaction__id=self.message.context_id).first()
            self.context_direct = True
        else:
            context_interaction = Interaction.objects.filter(
                member_account=self.sender).last()
            if context_interaction and context_interaction.fragment:
                context_piece = context_interaction.fragment.piece

        self.written = getattr(context_piece, "written", None)
        self.default_extra = getattr(context_piece, "default_extra", None)

    def process(self):

        if self.message.text.startswith("/"):
            behavior_processor = BehaviorProcessor(
                self.message.text[1:], self.response)
            behavior_processor.process()
            return

        self.response.message_text("hola mundo")

        return

    def intension(self):

        if self.context_direct and self.written:
            # intencion directa por written
            pass

        elif self.context_direct and self.default_extra:
            # intencion directa por default_extra, evaluar destino
            pass

        intent_to_contact_administrator = self.intent_to_contact_administrator()
        valid_time_interval = self.message.valid_time_interval(
            raise_exception=False
        )

        if self.written or self.default_extra:
            # intencion indirecta, se requiere mas analisis por written
            # evaluacion de tiempo
            # evaluacion de intencion de contacto con administrador
            pass

    def intent_to_contact_administrator(self) -> bool:
        return bool(re.search(r"admin", self.message.text, re.IGNORECASE))

    # def process_(self):

    #     if self.sender.is_staff:
    #         if self.text.startswith(("/", "#", "*")):
    #             self.handle_staff()
    #             return

    #     elif not self.can_response():
    #         return

    #     try:

    #         if self.message.text.startswith("/"):
    #             self.handle_commands()

    #         self.handle_text_message()
    #         # else:
    #         #     self.sender.send_simple_message("No entendí el mensaje")

    #     except Exception as e:
    #         import traceback
    #         error_ = traceback.format_exc()
    #         if self.api_request.error_text is None:
    #             self.api_request.error_text = ""
    #         self.api_request.error_text += f"\n\n{error_}"
    #         self.api_request.save()

    # def can_response(self):
    #     sender_text_response = False
    #     if self.sender.status:
    #         sender_text_response = self.sender.status.text_response

    #     account_text_response = self.sender.account.text_response
    #     space_test = self.sender.account.space.test
    #     can_any = any(
    #         [sender_text_response, account_text_response, space_test])

    #     if can_any:
    #         return can_any

    #     if self.has_role_or_admin():
    #         return True
    #     self.response.api_record_in.add_error(
    #         {
    #             "error": "El usuario no tiene permisos de respuesta",
    #             "sender_text_response": sender_text_response,
    #             "account_text_response": account_text_response,
    #             "space_test": space_test
    #         }
    #     )

    # def has_role_or_admin(self):
    #     pass
    #     # active_admin_role = has_admin(self.sender=self.sender)
    #     # user_tester = "Testers" in self.sender.get_circles(flat=True)
    #     # if not (active_admin_role or user_tester):
    #     #     return

    # def handle_staff(self):
    #     if self.message.text.startswith("/"):
    #         self.handle_commands()
    #     elif self.message.text.startswith("#"):
    #         self.handle_message_query()
    #     elif self.message.text.startswith("*"):
    #         pass
    #         # DespachadorPayload(self.sender, self.message.text[1:])

    # def handle_message_query(self):
    #     msg_txt = self.message.text[1:].strip()
    #     # if msg_txt.isdigit():
    #     #     if Message.objects.filter(id=msg_txt).exists():
    #     #         Msg(self.sender, variables={"id": msg_txt})
    #     #     else:
    #     #         self.sender.send_simple_message("No se encontró el mensaje")
    #     # elif Message.objects.filter(name=msg_txt).exists():
    #     #     Msg(self.sender, variables={"name": msg_txt})
    #     # else:
    #     #     self.sender.send_simple_message(
    #     #         "este mensaje (%s) no ha sido creado" % self.message.text[1:])

    # def handle_commands(self):
    #     pass
    #     # if self.message.text == "/restart" or self.message.text == "/reanudar":
    #     #     restart(self.message.member_account)
    #     # elif self.message.text == "/reset" or self.message.text == "/reiniciar":
    #     #     reset_for_staff(self.message.member_account)
    #     # elif self.message.text == "/help" or self.message.text == "/ayuda":
    #     #     HelpCommands(self.message.member_account)
    #     # elif self.message.text == "/status":
    #     #     self.message.member_account.send_status_message()
    #     # elif self.message.text == "/request meta_data user":
    #     #     SenderStatusFull(self.message.member_account)
    #     # elif self.message.text == "/request meta_data":
    #     #     SenderStatusFull(self.message.member_account, variables={"user": False})
    #     # elif self.message.text == "/test" or self.message.text == "/probar":
    #     #     self.message.member_account.set_tester_config()

    # def handle_text_message(self):
    #     # comprovarcontexto del mensaje

    #     # respuesta a otros mensajes

    #     # intencion de hablar con un administrador humano

    #     # comprovar diccionarios de respuesta

    #     # ultimo mensaje
    #     if not self.manager_flow.response_list:
    #         pass
    #         # self.manager_flow.response_list.append(
    #         #     TextResponse(
    #         #         text="No entendí el mensaje",
    #         #         sender=self.sender,
    #         #         api_request=self.api_request
    #         #     )
    #         # )
