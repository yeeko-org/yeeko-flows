import json
from typing import Optional, Type

from django.conf import settings
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from pydantic import BaseModel


class GeminiClient:
    """Cliente delgado sobre google-genai para extracción con salida
    estructurada (JSON que cumple un esquema Pydantic).

    Adaptado de ocs-django-db/utils/gemini_ai.py, recortado a lo que el
    behavior ia_extrae necesita: una llamada con system prompt + esquema.
    Captura los errores de red/SDK en self.errors y devuelve None; quien
    llama decide cómo degradar (p. ej. repreguntar al usuario).
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.GEMINI_MODEL
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.errors: list[str] = []
        self.last_response = None

    def extract(
            self, system_prompt: str, user_text: str,
            schema: Type[BaseModel]
    ) -> Optional[dict]:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_json_schema=schema.model_json_schema(),
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
        )
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=user_text, config=config
            )
        except ClientError as e:
            self.errors.append(f"{e.message} (ClientError {e.status})")
            return None
        except Exception as e:
            self.errors.append(str(e))
            return None

        self.last_response = response
        return self._to_dict(response)

    @staticmethod
    def _to_dict(response) -> Optional[dict]:
        # Con response_json_schema (no response_schema) el SDK no rellena
        # .parsed, así que el camino normal es parsear el texto JSON.
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, BaseModel):
            return parsed.model_dump()
        if isinstance(parsed, dict):
            return parsed
        try:
            return json.loads(response.text)
        except (ValueError, AttributeError):
            return None
