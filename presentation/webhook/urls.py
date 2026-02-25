from django.urls import path

from presentation.webhook.whatsapp import WhatsappMessageView
from presentation.webhook.messenger import MessengerWebhookView


urlpatterns = [
    path(
        'whatsapp/webhook_fb_message', WhatsappMessageView.as_view(),
        name='webhook_meta_whatsapp'
    ),
    path(
        'messenger/webhook_meta_message', MessengerWebhookView.as_view(),
        name='webhook_meta_messenger'
    ),
]
