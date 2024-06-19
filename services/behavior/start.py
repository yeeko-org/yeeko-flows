from services.processor.behavior import BehaviorProcessor
from services.response.abstract import ResponseAbc


class StartBehavior:
    def __init__(
            self, response: ResponseAbc, default_message=None,
            behavior_name_default="start", **kwargs
    ):
        if default_message:
            response.message_text(default_message)

        try:
            BehaviorProcessor(behavior_name_default, response).process()
        except Exception as e:
            response.api_record_in.add_error({}, e)
