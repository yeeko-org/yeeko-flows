import json
from pprint import pprint
from django.conf import settings
from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from yeeko_abc_message_models.messenger.request import MessengerRequest


from interface.messenger.request import RecordMessengerRequest
from interface.messenger.response import MessengerResponse
from services.manager_flow import ManagerFlow


class MessengerWebhookView(generic.View):

    def get(self, request, *args, **kwargs):
        webhook_token_whatsapp = getattr(
            settings, "WEBHOOK_TOKEN_MESSENGER", None
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
            print("incoming_message -------------------------------------")
            pprint(incoming_message)

            request = MessengerRequest(incoming_message)
            request_record = RecordMessengerRequest(request)

            manage = ManagerFlow(
                request_record=request_record,
                response_class=MessengerResponse
            )
            manage()

        except Exception as e:
            print(e)

        return HttpResponse()
