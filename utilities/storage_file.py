import os
from uuid import uuid4

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile


def upload_file_to_storage(
        file, sub_path="", unique_name=True
) -> str:
    if unique_name:
        file_name = f"{uuid4()}_{file.name}"
    else:
        file_name = file.name
    full_path = os.path.join(sub_path, file_name)

    file_path = default_storage.save(full_path, file)
    file_url = default_storage.url(file_path)

    return file_url
