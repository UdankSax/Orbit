import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL is not set"
    )


engine = create_engine(

    DATABASE_URL,

    connect_args={
        "sslmode": "require"
    },

    pool_pre_ping=True,

    pool_recycle=1800
)


SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine
)