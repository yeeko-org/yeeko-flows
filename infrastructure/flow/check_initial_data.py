from django.conf import settings


class CheckInitialData:
    def __init__(self) -> None:
        from infrastructure.flow.models import Flow
        print("-----------Checking initial data for Flow-----------")
        Flow.objects.get_or_create(name="Notification")
        Flow.objects.get_or_create(name="Templates")
        # add more Flow here
