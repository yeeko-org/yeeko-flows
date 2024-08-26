from infrastructure.tool.views import Text, ManyButtons, FewButtons
from infrastructure.member.views import SenderManipulation


class GenericBase:
    member: SenderManipulation = None

    def __init__(self, member_utils):
        self.member = member_utils


class GetStartedPayload(GenericBase):
    alternative_welcome = (
        "¡Hola! 👋 Es un gusto saludarte. ¿Cómo podemos ayudarte?")
    # welcome = ("¡Hola %s! Por este medio podrás participar en algunos "
    #            "temas y preguntas de %s" % (sender.user_name(), page.title))
    welcome = ("¡Hola! Por este medio podrás participar en algunos "
               "temas y preguntas de nuestro espacio")
    title = ("¿Quieres comenzar a participar y mantenerte al tanto "
             "de lo que se proponga?")
    img_welcome = ("https://s3-us-west-2.amazonaws.com/cdn-yeeko/"
                   "static/img/bot/BIENVENIDA.png")

    def __call__(self):
        txt = Text(self.member, text_body=self.alternative_welcome)
        txt.send_message()


class KnowMorePayload(GenericBase):
    title = (
        "Hola, soy un chat-bot construído para facilitar la participación "
        # "de las personas involucradas en \"{0.title}\", lo haré a través "
        "de las personas involucradas en este espacio, lo haré a través "
        "de la interacción por botones con opciones que te iré preguntando. "
        "También puedes navegar con un menú debajo de este chat, donde "
        "siempre podrás volver a  ver las preguntas o los temas. Es muy "
        "importante que para que puedas participar, vayas eligiendo "
        "algunas de las opciones que te iremos ofreciendo. Creemos que "
        # "estás listo para comenzar, gracias por estar aquí {1}!"
        "estás listo para comenzar, gracias por estar aquí!")
    title_button = "¿Cómo quiero continuar?"
    interaction_type = "few_buttons"

    def __call__(self):
        Text(self.member, text_body=self.title).send_message()

        few_buttons = FewButtons(
            self.member, text_body=self.title_button)
        few_buttons.add_reply(
            title="Sí participar", payload="AcceptanceNotification")
        few_buttons.send_message()


# def AcceptanceNotification(sender, variables={}, countdown=0):
#     sender.update(push_subscription=True, subscribe=True)
#     from bot_core.messYeeko import Yeekos
#
#     countdown=sender.send_simple_message(f"¡Bien! A partir de ahora eres "
#         f"parte de las decisiones de '{sender.pageP.title}', eventualmente "
#         "te informaremos cuando exista informacion relevante",
#         typing=True, countdown=countdown)
#
#     countdown=sender.send_b_message("¡Gracias por suscribirte!",
#        [{
#             "type": "postback",
#             "title": icBell + "Configurar alertas",
#             "payload": "SetAlerts"
#         },], countdown=countdown, typing=True)
#
#     from bot_core.messYeeko import Yeekos
#     return Yeekos(sender, variables={"header":"¡Ahora sí estamos listos! "
#         "Selecciona uno de los Yeekos:",
#         "settings":{"text_response":True}, "image_title":False},
#         countdown=countdown)


# def HelpA(sender, variables={}, countdown=0):
#     isYeeko=True if settings.FB_MAIN_PAGE==sender.pageP.pid else False
#     botones=BRR([["¿Cómo crear Yeekos?", "HowYeeko"]]) if isYeeko else []
#     botones.extend(BRR([
#         ["¿Cómo Proponer?", "HowProposal"],
#         ["¿Cómo Votar?", "HowVote"],
#         ["¿Cómo Comentar?", "HowComment"]   ]))
#     return sender.send_rrb_message(txt("HelpA"), botones, countdown=countdown,
#         typing=False)
#
