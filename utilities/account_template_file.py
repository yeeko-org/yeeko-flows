from pprint import pprint
from infrastructure.box.models import Piece
from infrastructure.place.models import Account
from interface.whatsapp.account_template import AccountTemplate
from interface.whatsapp.message_template import MessageTemplate

account = Account.objects.get(pk=102141056009039)

# account_template_file = AccountTemplate(
#     account=account,
# )

# account_template_file.get_templates()
# account_template_file.fetch_templates()

piece = Piece.objects.get(pk=49)
message_template = MessageTemplate(account, piece)

pprint(message_template.make_message())

message_template.send_message(phone_to="525513375592")
