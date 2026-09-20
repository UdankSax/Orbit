import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# -------------------------
# Environment
# -------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set"
    )


# -------------------------
# Database Engine
# -------------------------

engine = create_engine(
    DATABASE_URL,

    connect_args={
        "sslmode": "require"
    },

    # Check whether a connection is still alive
    # before SQLAlchemy gives it to the application.
    pool_pre_ping=True,

    # Don't keep connections around indefinitely.
    pool_recycle=1800,
)


# -------------------------
# Session
# -------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)