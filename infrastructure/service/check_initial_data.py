from django.conf import settings

PLATFORM_NAME_FOR_NOTIFICATION = getattr(
    settings, 'PLATFORM_NAME_FOR_NOTIFICATION', "notification")

PLATFORM_NAME_FOR_DASHBOARD = getattr(
    settings, 'PLATFORM_NAME_FOR_DASHBOARD', "dashboard")


class CheckInitialData:
    def __init__(self) -> None:
        from infrastructure.service.models import Platform
        print("-------------Checking initial data for Platform-------------")
        Platform.objects.get_or_create(name="whatsapp")
        Platform.objects.get_or_create(name=PLATFORM_NAME_FOR_NOTIFICATION)
        Platform.objects.get_or_create(name=PLATFORM_NAME_FOR_DASHBOARD)
