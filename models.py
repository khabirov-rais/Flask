import atexit
import datetime
import os
from typing import List

from sqlalchemy import create_engine, String, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column, Mapped, relationship
from werkzeug.security import generate_password_hash, check_password_hash

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_DB = os.getenv("POSTGRES_DB", "pg_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5454")

PG_DSN = (f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:'
          f'{POSTGRES_PORT}/{POSTGRES_DB}')

engine = create_engine(PG_DSN)

Session = sessionmaker(bind=engine)

atexit.register(engine.dispose)


class Base(DeclarativeBase):
    pass


class Ads(Base):
    __tablename__ = "app_ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"))
    user: Mapped[List["User"]] = relationship(back_populates="owner")

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "user": self.user.name,
            "user_id": self.user.id,
            "user_email": self.user.email
        }


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    owner: Mapped["Ads"] = relationship(back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }


Base.metadata.create_all(bind=engine)
