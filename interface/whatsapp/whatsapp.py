from django.utils import timezone
import json
import time
from typing import Any, Optional
from django.conf import settings

from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction


class WhatsappMessage:
    def __init__(self, request: Any) -> None:
        self.show_prints: bool = getattr(
            settings, "SHOW_POST_WA_PRINTS", False)
        self.platform_name: str = "whatsapp fb"
        self.api_data: Optional[dict] = None
        self.msg_body: Optional[str] = None
        self.phone_number_id: Optional[str] = None
        self.message_sid: Optional[str] = None
        self.original_sid: Optional[str] = None
        self.account: Optional[Account] = None
        self.interaction: Optional[Interaction] = None
        self.trigger: Optional[Any] = None
        self.payload: Optional[Any] = None
        self.member_account: Optional[Any] = None
        self.sender: Optional[Any] = None
        self.is_new_sender: bool = False
        self.profile_name: Optional[str] = None

        self.parse_request_body(request)
        self.print_request_body(request)

    def __call__(self, *args, **kwargs):
        error_api = self.get_api_data()
        if error_api:
            if self.show_prints:
                print("error_api:", error_api)
            return self.send_response(error_api)

        self.process_statuses()

        messages = self.api_data.get("messages")
        if not messages:
            return self.send_response(
                "Da otra cosa en whatsapp_business_api_data")

        self.process_messages()
        self.process_interaction()
        self.process_message_type()
        self.process_account()

    

    def parse_request_body(self, request):
        self.req_body = json.loads(request.body)
        self.timestamp_server = int(time.time())
        self.api_request = ApiRecord(
            platform_id=self.platform_name,
            body=self.req_body,
            is_incoming=True,
            created=timezone.now())

    def print_request_body(self, request):
        if self.show_prints:
            print("----------------")
            print(request.body)
            print("----------------")

    def process_messages(self):
        messages = self.api_data.get("messages")
        if not messages:
            return self.send_response(
                "Da otra cosa en whatsapp_business_api_data")

        self.extract_phone_number_id()
        self.extract_contact_info()
        self.process_curr_message()
        self.find_account()
        self.handle_no_account()

    def extract_phone_number_id(self):
        self.phone_number_id = self.api_data.get("phone_number_id")
        if not self.phone_number_id:
            self.phone_number_id = self.api_data.get(
                "metadata", {}).get("phone_number_id")
        if self.show_prints:
            print("phone_number_id:", self.phone_number_id)

    def extract_contact_info(self):
        try:
            curr_contact = self.api_data["contacts"][0]
            wa_id = curr_contact["wa_id"]
            self.profile_name = curr_contact["profile"]["name"]
        except Exception as e:
            print("algún error en contacts:\n %s" % e)

    def process_curr_message(self):
        curr_message = self.api_data["messages"][0]
        http_response = self.get_base_info(curr_message, is_status=False)
        if http_response:
            print("error 1")
            return http_response

    def find_account(self):
        try:
            self.account = Account.objects.get(pid=self.phone_number_id)
        except Account.DoesNotExist:
            print("No se encontró la cuenta")

    def handle_no_account(self):
        if not self.account:
            http_response = self.message_check_v4()
            if http_response:
                print("error 2")
                return http_response

    def process_statuses(self):
        statuses = self.api_data.get("statuses")
        if statuses:
            curr_status = statuses[0]
            return self.save_status(curr_status)

    def process_interaction(self):
        if self.message_sid:
            self.interaction = Interaction(mid=self.message_sid)

        context = curr_message.get("context", {})
        self.original_sid = context.get("id")

    def process_message_type(self):
        type_message = curr_message.get("type")
        http_response = self.save_message(type_message, curr_message)
        if http_response:
            print("error 3")
            return http_response

    def process_account(self):
        http_response = self.get_member_account(curr_message)
        if http_response:
            print("error 4")
            return http_response

        if self.account:
            print("proceso 5")
            http_response = self.send_response()
            BoxView(self)()
            return http_response
        else:
            return self.send_payload_v4()

    def get_api_data(self):
        try:
            curr_change = self.req_body["entry"][0]["changes"][0]
            field = curr_change["field"]
            value = curr_change["value"]
            if field == "messages":
                self.api_data = value.get("whatsapp_business_api_data", value)
                if "errors" in self.api_data:
                    self.api_request.errors = self.api_data["errors"]
                    return "Recibimos errores, debemos guardarlos, aún no lo hacemos"
            else:
                return "No hay whatsapp_business_api_data"
        except Exception as e:
            return f"No extrajimos alguna cosa básica: {e}"
        return None

    def message_check_v4(self):
        from bot_user.models import UserMessengerCommit
        if UserMessengerCommit.objects.filter(mid=self.message_sid).exists():
            return self.send_response(
                "Recibimos otra vez algo que ya estaba registrado")
        return None

    def get_base_info(self, obj, is_status=False):
        max_time = 60000 if is_status else 30000
        timestamp = int(obj.get("timestamp"))
        self.api_request.datetime = timestamp
        if timestamp > self.timestamp_server + max_time:
            return self.send_response("YA TE PASASTE, ES MUCHO TIEMPO")
        self.message_sid = obj.get("id")
        return None

    def save_message(self, type_message, curr_message):
        button_payloads = {}
        msg_sent = None
        if type_message == "button" or type_message == "interactive":
            if not self.account:
                # if self.original_sid:
                #     built_reply = None
                try:
                    msg_sent = MsgSend.objects.get(mid=self.original_sid)
                    button_payloads = msg_sent.button_payloads
                except MsgSend.DoesNotExist:
                    print(f"NO SE ENCONTRÓ EL MsgSend;"
                          f"mid: {self.original_sid}; type: {type_message}")
                except Exception as e:
                    print(f"HAY OTRO ERROR DESCONOCIDO: {e}")
                    print(f"mid: {self.original_sid}; type: {type_message}")
        if self.original_sid and self.account:
            try:
                interaction_reply = Interaction.objects.get(
                    mid=self.original_sid)
                self.member_account = interaction_reply.member_account
                self.trigger = Trigger(
                    interaction_reply=interaction_reply,
                    is_direct=True)
            except Exception as e:
                self.api_request.error = "Interacción no encontrada"
                self.api_request.errors = [
                    f'mensaje no encontrado: {self.message_sid}',
                    f'error: {e}']

        if type_message == "text":
            self.api_request.interaction_type_id = "text"
            self.msg_body = curr_message["text"]["body"]
        elif type_message == "button" and not self.account:
            button = curr_message.get("button", {})
            payload_text = button.get("payload")
            self.payload = button_payloads.get(payload_text)
            self.api_request.interaction_type_id = "button"
            if not self.payload:
                print(f"No se encontró el payload: "
                      f"\n msg_sent: {msg_sent}"
                      f"\n payload_text: {payload_text}")
            if self.show_prints:
                print("button: \n", button)
        elif type_message == "interactive" or type_message == "button":
            interactive_type = "button"
            if type_message == "interactive":
                interactive = curr_message.get("interactive", {})
                interactive_type = interactive["type"]
                prev_payload = interactive[interactive_type]
                payload_id = prev_payload["id"]
                # complement = 'reply' if interactive_type_wa == 'list_reply' else 'button'
                # interactive_type = f"interactive_{complement}"
            else:
                button = curr_message.get("button", {})
                prev_payload = button
                payload_id = button["payload"]
            self.api_request.interaction_type_id = interactive_type
            if self.account:
                self.interaction.interaction_type_id = interactive_type
                self.interaction.reference = prev_payload
                try:
                    built_reply = BuiltReply.objects.get(uuid=payload_id)
                    if not self.trigger:
                        self.trigger = Trigger(is_direct=True)
                    self.member_account = built_reply.interaction.member_account
                    self.trigger.built_reply = built_reply
                except Trigger.DoesNotExist:
                    # RICK 5: Deberíamos mandarle un menaje de no registro
                    self.api_request.errors = [f'mensaje {self.message_sid}']
                    return self.send_response("No se encontró el trigger")
            else:
                self.payload = button_payloads.get(payload_id)
                if not self.payload:
                    print(f"No se encontró el payload: "
                          f"\n msg_sent: {msg_sent}"
                          f"\n payload_id: {payload_id}")
        elif type_message == "reaction":
            self.api_request.interaction_type_id = "reaction"
            if self.account:
                emoji = curr_message.get("reaction", {}).get("emoji")
                return self.save_reaction(emoji)
            else:
                return self.send_response("No se guardan reacciones")
        elif type_message == "ephemeral":
            return self.send_response("No se guardan ephemeral")
        # elif type_message == "sticker":
        #     print("Recibimos un sticker que por ahora no registramos")
        #     print(curr_message)
        #     sticker_id = curr_message.get("sticker", {}).get("id")
        else:
            try:
                interaction_type = InteractionType.objects.get(
                    name=type_message)
                self.api_request.interaction_type = interaction_type
                if interaction_type.group_type == "media":
                    http_response = self.save_media(
                        curr_message, interaction_type)
                    if http_response:
                        return http_response
                else:
                    return self.send_response(
                        f"No se guarda el tipo {type_message}")
            except InteractionType.DoesNotExist:
                error = f"El type_message no existe: {type_message}"
                return self.send_response(error)
            # print("En MEDIA, se puede recibir:")
            # print("context, identity, media, location, contacts, system")
            # print("image, sticker")
            # print("También se pueden recibir unknow")
            # print(curr_message)
            # return HttpResponse()
        return None

    def save_status(self, curr_status):
        need_finish = self.get_base_info(curr_status, is_status=True)
        print("save_status", curr_status)
        if need_finish:
            return self.send_response()
        msg_status = curr_status["status"]
        if not msg_status:
            return self.send_response("No hay status")
        conversation = curr_status.get("conversation")
        pricing = curr_status.get("pricing")
        error = None
        try:
            original_interaction = Interaction.objects.get(
                mid=self.message_sid)
            try:
                Event.objects.create(
                    event_name=msg_status,
                    timestamp=self.api_request.datetime,
                    interaction=original_interaction,
                    date=timezone.now())
            except Exception as e:
                error = (f"No se pudo crear el evento:\n {e};\n"
                         f"msg_status: {msg_status};\n"
                         f"interaction: {original_interaction.mid}")
        except Interaction.DoesNotExist:
            try:
                msg_send = MsgSend.objects.get(mid=self.message_sid)
                fields = ["sent", "delivered", "read"]
                if msg_status in fields:
                    setattr(msg_send, f"date_{msg_status}", timezone.now())
                    msg_send.save()
                else:
                    error = f"status no en sistema {msg_status}"
            except Exception as e:
                error = f"No se encontró la interacción {self.message_sid}"
        return self.send_response(error)

    def save_reaction(self, emoji):
        error = None
        try:
            original_interaction = Interaction.objects.get(
                mid=self.original_sid)
            try:
                # RICK 5: Falta el timestamp
                Event.objects.create(
                    event_name="reaction",
                    interaction=original_interaction,
                    emoji=emoji,
                    date=timezone.now())
            except Exception as e:
                error = (f"No se pudo crear el evento:\n {e};\n"
                         f"emoji: {emoji};\n"
                         f"interaction: {original_interaction.mid}")
        except Interaction.DoesNotExist:
            error = f"No se encontró la interacción {self.original_sid}"
        return self.send_response(error)

    def save_media(self, curr_message, interaction_type):
        # RICK 5: Voy a dejarlo pendiente
        return self.send_response("No se guardan mensajes de media")

    def get_member_account(self, curr_message):
        from bot_page.models import PagePremium
        from django.contrib.auth.hashers import make_password
        from users.models import User
        from perfil.models import Settings, Role

        whatsapp_from = curr_message.get("from")
        user_created = None

        def get_user(args):
            if self.show_prints:
                print("Argumentos para encontrar usuario:", args)
            try:
                user_obj = User.objects.get(**args)
                usr_created = False
            except User.DoesNotExist:
                value = args.get("email", whatsapp_from)
                private_hash = getattr(settings, "PRIVATE_HASH")
                args.update({
                    "password": make_password(value + private_hash),
                    "username": value,
                    "first_name": self.profile_name,
                    "last_name": "",
                    "phone": whatsapp_from,
                })
                user_obj = User.objects.create(**args)
                Settings.objects.filter(
                    user=user_obj).update(
                    gender="undefined")
                usr_created = True
            if self.show_prints:
                print("usr_created:", usr_created)
            return user_obj, usr_created

        def send_error(user_obj, error):
            error_text = f"Error al crear sender: {error}"
            if user_created is True:
                user_obj.delete()
            return self.send_response(error_text)

        if self.account:

            def create_member():
                default_role = Role.objects.get(name="normal")
                new_member = Member.objects.create(
                    user=user, space=self.account.space,
                    role=default_role)
                return new_member

            def create_member_account(member_obj):
                self.is_new_sender = True
                new_member_account = MemberAccount.objects.create(
                    account=self.account, member=member_obj, status_id='chatbot')
                return new_member_account

            if self.member_account:
                if self.show_prints:
                    print("member_account:", self.member_account)
                return None
            user, user_created = get_user({"phone": whatsapp_from})
            if not user_created:
                try:
                    self.member_account = MemberAccount.objects\
                        .get(account=self.account, member__user=user)
                    self.is_new_sender = False
                except MemberAccount.MultipleObjectsReturned:
                    self.member_account = MemberAccount.objects\
                        .filter(account=self.account, member__user=user)\
                        .order_by("id").first()
                    print("!!Hay varios MemberAccount, se tomó el primero")
                except MemberAccount.DoesNotExist:
                    try:
                        member = Member.objects.get(
                            user=user, space=self.account.space)
                    except Member.DoesNotExist:
                        member = create_member()
                    except Exception as e:
                        return send_error(user, e)
                    self.member_account = create_member_account(member)
            else:
                member = create_member()
                self.member_account = create_member_account(member)
        else:
            try:
                self.sender = UserMessenger.objects.get(
                    idMessenger=whatsapp_from,
                    pageP__phone_number_id=self.phone_number_id,
                    platform__name=self.platform_name)
            except Exception as e:
                print(e)
            if not self.sender:
                try:
                    page = PagePremium.objects.get(
                        phone_number_id=self.phone_number_id)
                except Exception as e:
                    print(
                        "No hay una página que coincida con las configuraciones",
                        e)
                    return HttpResponse()
                email = f"{whatsapp_from}@tw.yeeko.org"
                user, user_created = get_user({"email": email})
                try:
                    self.sender, self.is_new_sender = UserMessenger.objects.get_or_create(
                        idMessenger=whatsapp_from,
                        pageP=page,
                        user=user,
                        platform_id=self.platform_name)
                except Exception as e:
                    return send_error(user, e)
                if self.is_new_sender:
                    self.sender.text_response = self.sender.pageP.init_text_response
                    self.sender.add_user_extra(
                        data={"phone": whatsapp_from},
                        data_type="user_config",
                        origin="whatsapp")
        return None

    def send_payload_v4(self):
        from bot_user.models import UserMessengerCommit
        from bot_core.despachadores import DespachadorText, DespachadorPayload
        from bot_core.utilidades import jLoad
        from django.template.defaultfilters import slugify

        if not self.is_new_sender and not self.payload:
            extra_config = jLoad(self.sender.extra_data)
            whatsapp_payload = extra_config.get("whatsapp_payload", {})
            body_slug = slugify(self.msg_body)
            self.payload = whatsapp_payload.get(body_slug, False)
        if self.payload:
            commit = UserMessengerCommit.objects.create(
                userMessenger=self.sender,
                typeCommit="Payload",
                commit=self.payload,
                mid=self.message_sid,
                request_body=self.req_body,
            )
            self.sender.text_response = True
            DespachadorPayload(self.sender, self.payload, commit=commit)
            if self.show_prints:
                print("DespachadorPayload")
        if self.msg_body and not self.payload:
            commit = UserMessengerCommit.objects.create(
                userMessenger=self.sender,
                typeCommit="Text",
                commit=self.msg_body,
                mid=self.message_sid,
                request_body=self.req_body,
            )
            if self.is_new_sender:
                self.sender.statusMess = "get_started"
            elif not UserMessengerCommit.objects.filter(
                    userMessenger=self.sender, typeCommit="Payload").exists():
                self.sender.statusMess = "get_started"
            DespachadorText(self.sender, self.msg_body, commit=commit)
            if self.show_prints:
                print("DespachadorText", self.msg_body)
        if not self.msg_body and not self.payload:
            return self.send_response(
                "El mensaje no trajo las opciones esperadas")
        self.sender.post_interaction_checking_date()
        print("send_payload_v4 final")
        return self.send_response()

    def send_response(self, error=None):
        # import traceback
        # import sys

        from bot_fb_messenger.fbAPI import post_wa_read
        from box.views import get_message_link
        api_request = None
        if error and self.show_prints:
            print("error:", error)
        try:
            if error:
                if not self.api_request.interaction_type_id:
                    self.api_request.interaction_type_id = "error"
                self.api_request.error = error
            self.api_request.response_status = 400 if error else 200
            self.api_request.success = bool(not error)
            self.api_request.save()
            api_request = self.api_request
        except Exception as e:
            # error_ = traceback.format_exc()
            print(f"!!!!No se pudo guardar el api request: {e};\n "
                  f"data: {self.req_body};\nerror: {error}")
            # print("Error:", error_)
        if self.interaction:
            if not self.interaction.interaction_type_id:
                self.interaction.interaction_type_id = (
                    self.api_request.interaction_type_id)
            try:
                if self.trigger:
                    self.trigger.save()
                elif self.is_new_sender:
                    message_link = get_message_link(
                        self.account, self.msg_body)
                    if message_link:
                        self.trigger = Trigger.objects.create(
                            message_link=message_link)
                    else:
                        print("Es nuevo pero no se guardó el trigger")
                else:
                    last_bot_interaction = Interaction.objects\
                        .filter(member_account=self.member_account,
                                is_incoming=False)\
                        .last()
                    if last_bot_interaction:
                        self.trigger = Trigger.objects.create(
                            interaction_reply=last_bot_interaction)
                if self.trigger:
                    self.interaction.trigger = self.trigger
                self.interaction.member_account = self.member_account
                self.interaction.save()
                if api_request:
                    self.interaction.api_requests.add(api_request)
            except Exception as e:
                print(f"!!!!No se pudo guardar la interacción: {e};\n "
                      f"data: {self.req_body};\nerror: {error}")
        if self.message_sid:
            post_wa_read(self.phone_number_id, self.message_sid)

        return HttpResponse()
