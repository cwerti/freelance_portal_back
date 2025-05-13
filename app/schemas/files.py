import fastapi
import pydantic

from schemas.core import Model


class NewFile(Model):
    name: str
    path: str
    is_image: bool
