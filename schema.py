import pydantic
from typing import Optional
from abc import ABC

class AbstractUser(pydantic.BaseModel, ABC):
    name: str
    password: str
    email: str

    @pydantic.field_validator('password')
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError(f'Минимальный размер пароля 10 символов')
        return v


class CreatesUser(AbstractUser):
    name: str
    password: str
    email: str

class UpdateUser(AbstractUser):
    name: Optional[str] = None
    password: Optional[str] = None
