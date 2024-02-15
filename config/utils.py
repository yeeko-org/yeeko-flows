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

    return env_value.lower() == "true"


def getenv_db(
        env_pref: str = "DATABASE", is_postgres: bool = True,
        base_dir: Optional[Path] = None
) -> dict:
    database_name = os.getenv(f"{env_pref}_NAME", "db.sqlite3")
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
        if base_dir:
            database_name = base_dir / database_name

        return {
            'ENGINE': 'django.db.backends.sqlite3', 'NAME': database_name
        }
