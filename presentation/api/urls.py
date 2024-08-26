from django.urls import path
from presentation.api.whatsapp.platform_template.send_message import (
    WhatsAppSendMessageTemplate)
from presentation.api.whatsapp.send_message.views import (
    WhastappSendSimpleMessage)


urlpatterns = [
    path('whatsapp/send-message-template/',
         WhatsAppSendMessageTemplate.as_view({'post': 'create'}),),
    path('whatsapp/send-simple-message/',
         WhastappSendSimpleMessage.as_view({'post': 'create'}),),
]
