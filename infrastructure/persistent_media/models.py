from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
import requests
from django.utils import timezone

from infrastructure.place.models import Account


def get_media_path(instance: "Media", filename):
    return f"media/{instance.account.pid}/{instance.media_type}/{filename}"


class Media(models.Model):
    CHOICES_TYPE = (
        ("image", "image"),
        ("video", "video"),
        ("audio", "audio"),
        ("document", "document"),
        ("sticker", "sticker"),
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_media_path)
    media_type = models.CharField(max_length=20, choices=CHOICES_TYPE)
    name = models.CharField(max_length=100, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    media_id = models.CharField(max_length=100, blank=True, null=True)
    uploaded_media_id_at = models.DateTimeField(blank=True, null=True)
    expiration_days = models.IntegerField(default=30)

    def __str__(self):
        return self.get_name()

    def save(self, *args, **kwargs):
        _ = super().save(*args, **kwargs)
        if not self.media_id:
            self.upload_media_file(save=False)
        return super().save(*args, **kwargs)

    def get_name(self):
        return self.name or self.file.name

    def get_expiration_date(self):
        return ((self.uploaded_media_id_at or timezone.now()) +
                timezone.timedelta(days=self.expiration_days-1))

    def get_media_id(self):
        if not self.media_id or timezone.now() > self.get_expiration_date():
            self.upload_media_file()

        if self.media_id and timezone.now() < self.get_expiration_date():
            return self.media_id
        return None

    def upload_media_file(self, save=True):
        media_id = None

        if self.account.platform_id == "whatsapp":  # type: ignore
            FACEBOOK_API_VERSION = getattr(
                settings, "FACEBOOK_API_VERSION", "v13.0")
            FACEBOOK_API_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"
            url = f"{FACEBOOK_API_URL}/{self.account.pid}/media"
            headers = {
                "Authorization": f"Bearer {self.account.token}"
            }
            media_extension = self.file.name.split(".")[-1]
            if media_extension == "jpg":
                media_extension = "jpeg"

            supported_media_types = {
                "image": ["jpeg", "png"],
                "video": ["mp4", "3gp"],
                "audio": ["aac", "amr", "mp3", "m4a", "ogg"],
                "document": [
                    "txt", "xls", "xlsx", "doc", "docx", "ppt", "pptx", "pdf"
                ],
                "sticker": ["webp"]
            }

            document_type_mime = {
                "txt": "text/plain",
                "xls": "application/vnd.ms-excel",
                "xlsx": "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet",
                "doc": "application/msword",
                "docx": "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document",
                "ppt": "application/vnd.ms-powerpoint",
                "pptx": "application/vnd.openxmlformats-officedocument."
                        "presentationml.presentation",
                "pdf": "application/pdf"
            }
            audio_type_mime = {
                "aac": "audio/aac",
                "amr": "audio/amr",
                "mp3": "audio/mpeg",
                "m4a": "audio/mp4",
                "ogg": "audio/ogg"
            }

            supported_type = supported_media_types.get(self.media_type, [])
            if media_extension not in supported_type:
                if not save:
                    raise ValueError(
                        f"Unsupported media type {self.media_type} "
                        f"with extension {media_extension}")
                return

            mime_type = f"{self.media_type}/{media_extension.lower()}"
            if self.media_type == "sticker":
                mime_type = f"image/{media_extension.lower()}"
            elif self.media_type == "document":
                mime_type = document_type_mime.get(media_extension)
            elif self.media_type == "audio":
                mime_type = audio_type_mime.get(media_extension)

            file_path = self.file.__str__()
            with default_storage.open(file_path, "rb") as file:
                files = {
                    "file": (self.file.name, file, mime_type),
                }
                data = {
                    "messaging_product": "whatsapp",
                    "type": f"{self.media_type}/{media_extension.lower()}"
                }

                response = requests.post(
                    url, data=data, headers=headers, files=files)  # type: ignore

                if response.status_code == 200:
                    media_id = response.json().get("id")
                else:
                    print(response.json())

        if media_id:
            self.media_id = media_id
            self.uploaded_media_id_at = timezone.now()
            if save:
                self.save()
