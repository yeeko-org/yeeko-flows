import json


def wa_form_reply_data(flow_token: str, selection: list) -> dict:
    """Build a WhatsApp webhook payload for a Flow completion
    (``interactive.type == "nfm_reply"``) carrying the given flow_token
    and selected option ids."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "112795704944207",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "phone_number_id": "103571329211620",
                                "display_phone_number": "15550578839",
                            },
                            "contacts": [
                                {
                                    "wa_id": "5215549468438",
                                    "profile": {"name": "Ricardo Sanginés"},
                                }
                            ],
                            "messages": [
                                {
                                    "id": "wamid.WAFORMTEST123",
                                    "from": "5215549468438",
                                    "timestamp": "1702960757",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "nfm_reply",
                                        "nfm_reply": {
                                            "name": "flow",
                                            "body": "Sent",
                                            "response_json": json.dumps(
                                                {
                                                    "flow_token": flow_token,
                                                    "selection": selection,
                                                }
                                            ),
                                        },
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
