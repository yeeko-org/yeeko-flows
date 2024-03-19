import re

# from bot_message.models import Message
# from bot_user.models import MsgSend, Answer
from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRequest
# from scripts.common import has_admin
# from proposals.models import Proposal
# from bot_core.models import BotError
# from .DespachadorPayload import DespachadorPayload
# from .OtherModule import languageFilter
from services.processor.processor_base import Processor
from services.request import RequestAbc
from services.request.message_model import MessageBase, TextMessage
from services.response import ResponseAbc


class TextMessageProcessor(Processor):
    sender: MemberAccount
    api_request: ApiRequest
    request_message_id: str
    message: TextMessage
    response: ResponseAbc

    def __init__(
            self, manager_flow, message: TextMessage, response: ResponseAbc
    ) -> None:
        self.manager_flow = manager_flow
        self.message = message
        if not response.sender:
            raise Exception("Message must have a member_account to process it")
        self.sender = response.sender

        self.response = response

    def process(self):

        self.text = self.message.text

        self.response.message_text("hola mundo")

        return

        if self.sender.is_staff:
            if self.text.startswith(("/", "#", "*")):
                self.handle_staff()
                return

        elif not self.can_response():
            return

        statusMess = ["get_started", "OPEN_ASK",
                      "IS_MANDATORY", "POTENTIAL_TRACKING", "YKS"]

        try:
            # if "Envía este mensaje para" in self.message.text:
            #     self.handle_topic_message(self.message.text)
            #     return

            if self.message.text.startswith("/"):
                self.handle_commands()
            # elif self.sender.statusMess in statusMess:
            #     self.handle_status(self.sender, self.message.text)

            self.handle_text_message()
            # else:
            #     self.sender.send_simple_message("No entendí el mensaje")

        except Exception as e:
            import traceback
            error_ = traceback.format_exc()
            if self.api_request.error_text is None:
                self.api_request.error_text = ""
            self.api_request.error_text += f"\n\n{error_}"
            self.api_request.save()

    def can_response(self):
        sender_text_response = False
        if self.sender.status:
            sender_text_response = self.sender.status.text_response

        account_text_response = self.sender.account.text_response
        space_test = self.sender.account.space.test
        can_any = any(
            [sender_text_response, account_text_response, space_test])

        if can_any:
            return can_any

        if self.has_role_or_admin():
            return True

        self.errors.append((
            "El usuario no tiene permisos de respuesta",
            {
                "sender_text_response": sender_text_response,
                "account_text_response": account_text_response,
                "space_test": space_test
            }
        ))

    def has_role_or_admin(self):
        pass
        # active_admin_role = has_admin(self.sender=self.sender)
        # user_tester = "Testers" in self.sender.get_circles(flat=True)
        # if not (active_admin_role or user_tester):
        #     return

    def handle_staff(self):
        if self.message.text.startswith("/"):
            self.handle_commands()
        elif self.message.text.startswith("#"):
            self.handle_message_query()
        elif self.message.text.startswith("*"):
            pass
            # DespachadorPayload(self.sender, self.message.text[1:])

    def handle_message_query(self):
        msg_txt = self.message.text[1:].strip()
        # if msg_txt.isdigit():
        #     if Message.objects.filter(id=msg_txt).exists():
        #         Msg(self.sender, variables={"id": msg_txt})
        #     else:
        #         self.sender.send_simple_message("No se encontró el mensaje")
        # elif Message.objects.filter(name=msg_txt).exists():
        #     Msg(self.sender, variables={"name": msg_txt})
        # else:
        #     self.sender.send_simple_message(
        #         "este mensaje (%s) no ha sido creado" % self.message.text[1:])

    # def handle_topic_message(self):

    #     all_topics = [
    #         {"short_name": "jovenes", "large_name": "Oportunidades a los jóvenes"},
    #         {"short_name": "democracia", "large_name": "Proteger la democracia"},
    #         {"short_name": "trabajo", "large_name": "Mejores trabajos para tu desarrollo"},
    #         {"short_name": "salud", "large_name": "Salud digna para tod@s"},
    #         {"short_name": "medioambiente", "large_name": "Medioambiente sano"},
    #         {"short_name": "educacion", "large_name": "Educación de calidad para tod@s"},
    #         {"short_name": "pobreza", "large_name": "Combate a la pobreza"},
    #         {"short_name": "mujeres", "large_name": "Igualdad sustantiva de género"},
    #         {"short_name": "seguridad", "large_name": "Seguridad"},
    #         {"short_name": "corrupcion", "large_name": "Combate a la corrupción"}
    #     ]
    #     msg_name = ""
    #     if "seguir participando en el tema:" in self.message.text:
    #         msg_name = "simplificada2"
    #     elif "comenzar a participar en el tema:" in self.message.text:
    #         msg_name = "simplificada1"
    #     for topic in all_topics:
    #         if topic["large_name"].lower() in self.message.text.lower():
    #             msg_name += "_" + topic["short_name"]
    #             payload = 'Msg {"name": "%s"}' % msg_name
    #             payload_intro = 'Msg {"name": "presentacion_simplificada"}'
    #             self.message.member_account.add_user_extra(
    #                 data={"selected_topic": topic["large_name"]},
    #                 cumulative=False, data_type="auxiliar")
    #             countdown = DespachadorPayload(self.message.member_account, payload_intro)
    #             UserMessengerCommit.objects.create(
    #                 userMessenger=self.message.member_account,
    #                 typeCommit="link_qr",
    #                 self.api_request=payload)
    #             return DespachadorPayload(
    #                 self.message.member_account, payload, countdown=countdown)

    def handle_commands(self):
        pass
        # if self.message.text == "/restart" or self.message.text == "/reanudar":
        #     restart(self.message.member_account)
        # elif self.message.text == "/reset" or self.message.text == "/reiniciar":
        #     reset_for_staff(self.message.member_account)
        # elif self.message.text == "/help" or self.message.text == "/ayuda":
        #     HelpCommands(self.message.member_account)
        # elif self.message.text == "/status":
        #     self.message.member_account.send_status_message()
        # elif self.message.text == "/por el poder de yeeko!雷":
        #     UserStaffPower(self.message.member_account)
        # elif self.message.text == "/request meta_data user":
        #     SenderStatusFull(self.message.member_account)
        # elif self.message.text == "/request meta_data":
        #     SenderStatusFull(self.message.member_account, variables={"user": False})
        # elif self.message.text == "/test" or self.message.text == "/probar":
        #     self.message.member_account.set_tester_config()
        # elif self.message.text.startswith("/link account"):
        #     self.message.member_account.link_account_with_code(self.message.text[13:])
        # elif "/demo " in self.message.text.lower():
        #     self.message.member_account.add_demo(self.message.text.replace("/demo ", "").strip())
        # elif self.message.text == "/yeekos":
        #     self.message.member_account.status()
        #     Yeekos(self.message.member_account)
        # elif re.match('/yeeko [0-9]+', self.message.text):
        #     self.message.member_account.status()
        #     yeeko_id = int(filter(str.isdigit, str(self.message.text)))
        #     DetallesYeeko(self.message.member_account, {"yeeko_id": yeeko_id})
        # elif re.match('/propuesta [0-9]+', self.message.text):
        #     proposal_id = int(filter(str.isdigit, str(self.message.text)))
        #     DetallesPropuesta(self.message.member_account, [proposal_id])

    # def handle_status(self, self.sender, self.message.text):
    #     statusMess = self.sender.statusMess
    #     if statusMess == "OTHERS":
    #         # Handle status "OTHERS"
    #         pass
    #     elif re.match('COMMENT [0-9]+', statusMess):
    #         # Handle comment status
    #         pass
    #     else:
    #         self.sender.send_simple_message("No entendí el mensaje")

    def handle_text_message(self):
        # comprovarcontexto del mensaje

        # respuesta a otros mensajes

        # intencion de hablar con un administrador humano

        # comprovar diccionarios de respuesta

        # ultimo mensaje
        if not self.manager_flow.response_list:
            pass
            # self.manager_flow.response_list.append(
            #     TextResponse(
            #         text="No entendí el mensaje",
            #         sender=self.sender,
            #         api_request=self.api_request
            #     )
            # )
