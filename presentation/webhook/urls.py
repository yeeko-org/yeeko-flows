from django.urls import path

from presentation.webhook.whatsapp import WhatsappMessageView

urlpatterns = [
    path(
        'whatsapp/webhook_fb_message', WhatsappMessageView.as_view(),
        name='webhook_meta_whatsapp'
    ),
]
