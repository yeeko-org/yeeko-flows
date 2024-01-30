import os
from typing import Optional, List


def getenv_list(
        env_name: str, default: Optional[List[str]] = None
) -> Optional[List[str]]:
    env_value = os.getenv(env_name)

    if env_value is None:
        return default

    return [field.strip() for field in env_value.split(",")]


def getenv_bool(env_name: str, default: bool = True) -> bool:
    env_value = os.getenv(env_name)
    if not env_value:
        return default

    return env_value.lower() == "true"
