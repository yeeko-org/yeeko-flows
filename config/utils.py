import os
from pathlib import Path
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

    return env_value.lower() in ["true", "1"]


def getenv_int(env_name: str, default: int = 0) -> int:
    env_value = os.getenv(env_name)
    if not env_value or not env_value.isdigit():
        return default

    return int(env_value)


def getenv_db(env_pref="DATABASE", is_postgres: bool = True) -> dict:
    database_name = os.getenv(f"{env_pref}_NAME")
    if is_postgres:
        return {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': database_name,
            'USER': os.getenv(f"{env_pref}_USER"),
            'PASSWORD': os.getenv(f"{env_pref}_PASSWORD"),
            'HOST': os.getenv(f"{env_pref}_HOST"),
            'PORT': int(os.getenv(f"{env_pref}_PORT", 5432)),
        }
    else:
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': database_name or "db.sqlite3"
        }
