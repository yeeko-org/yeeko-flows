from django.conf import settings


class CheckInitialData:
    def __init__(self) -> None:
        from infrastructure.xtra.models import ClassifyExtra, Format
        print("-----------Checking initial data for ClassifyExtra-----------")
        
        classifies = ["Notification", "Dashboard"]
        for classify in classifies:
            ClassifyExtra.objects.get_or_create(name=classify)

        formats = ["json", "int", "cv"]
        for format in formats:
            Format.objects.get_or_create(name=format)
