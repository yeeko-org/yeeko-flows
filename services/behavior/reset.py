from services.processor.behavior import BehaviorProcessor
from services.response.abstract import ResponseAbc


class ResetBehavior:
    def __init__(
            self, response: ResponseAbc, default_message=None,
            behavior_name_default="start", **kwargs
    ):
        response.message_text(
            default_message or "Tus Configuraciones sera reiniciadas, por "
            "favor espera un momento..."
        )
        response.sender.member.remove_all_extras()
        try:
            BehaviorProcessor(behavior_name_default, response).process()
        except Exception as e:
            response.add_error({}, e)
