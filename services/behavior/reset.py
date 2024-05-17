from services.processor.behavior_processor import BehaviorProcessor
from services.response.abstract import ResponseAbc

# @acl(only_staff=True, role=["admin"])
class ResetBehavior:
    def __init__(
            self, response: ResponseAbc, default_message=None,
            behavior_name_default="Started", **kwargs
    ):
        response.message_text(
            default_message or "Tus Configuraciones sera reiniciadas, por "
            "favor espera un momento..."
        )
        try:
            BehaviorProcessor(behavior_name_default, response).process()
        except Exception as e:
            response.api_record_in.add_error({}, e)
