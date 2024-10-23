from django.conf import settings


class CheckInitialData:
    def __init__(self) -> None:
        from infrastructure.xtra.models import ClassifyExtra
        print("-----------Checking initial data for ClassifyExtra-----------")
        ClassifyExtra.objects.get_or_create(name="Notification")
        ClassifyExtra.objects.get_or_create(name="Dashboard")
        # add more ClassifyExtra here
