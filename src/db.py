from __future__ import annotations

import getpass
import os
from urllib.parse import quote_plus

import pandas as pd

from .config import DEFAULT_POSTGRES_TABLE


def build_postgres_engine(
    db_name: str,
    db_user: str = "postgres",
    db_password: str | None = None,
    db_host: str = "localhost",
    db_port: str = "5432",
):
    try:
        from sqlalchemy import create_engine
    except ImportError as exc:
        raise ImportError(
            "SQLAlchemy is required for PostgreSQL mode. Install requirements.txt first."
        ) from exc

    password = db_password or os.getenv("PGPASSWORD")
    if password is None:
        password = getpass.getpass(f"Password for PostgreSQL user {db_user}: ")

    url = (
        f"postgresql+psycopg2://{db_user}:{quote_plus(password)}"
        f"@{db_host}:{db_port}/{db_name}"
    )
    return create_engine(url)


def read_dataset_from_postgres(
    db_name: str,
    db_user: str = "postgres",
    db_password: str | None = None,
    db_host: str = "localhost",
    db_port: str = "5432",
    table_name: str = DEFAULT_POSTGRES_TABLE,
) -> pd.DataFrame:
    engine = build_postgres_engine(
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        db_host=db_host,
        db_port=db_port,
    )
    return pd.read_sql(f"SELECT * FROM {table_name};", engine)
