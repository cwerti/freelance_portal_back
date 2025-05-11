import pydantic

from schemas.core import Model


class RegisterUserIn(Model):
    login: str = pydantic.Field(min_length=4)
    password: str = pydantic.Field(min_length=6)
    email: pydantic.EmailStr
    last_name: str
    first_name: str
    role_id: int



