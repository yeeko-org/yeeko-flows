import json
from django.conf import settings
from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from interface.whatsapp.request import WhatsAppRequest
from interface.whatsapp.response import WhatsAppResponse

from services.manager_flow import ManagerFlow


class WhatsappMessageView(generic.View):

    def get(self, request, *args, **kwargs):
        webhook_token_whatsapp = getattr(
            settings, "WEBHOOK_TOKEN_WHATSAPP", None
        )

        data: dict = request.GET or {}
        verify_token = data.get("hub.verify_token")
        mode = data.get("hub.mode")
        challenge = data.get("hub.challenge")

        all_valid_fields = all([
            webhook_token_whatsapp, verify_token, challenge,
            mode == "subscribe", webhook_token_whatsapp == verify_token
        ])

        if not all_valid_fields:
            return HttpResponse("error", status=403)

        return HttpResponse(challenge)

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            incoming_message = json.loads(self.request.body)
            print("incoming_message", incoming_message)
            manage = ManagerFlow(
                incoming_message,
                request_class=WhatsAppRequest,
                response_class=WhatsAppResponse
            )
            manage()

        except Exception as e:
            raise e

        return HttpResponse()
