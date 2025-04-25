import uuid
from typing import Any, TypeVar, Optional

import pydantic
from sqlalchemy.ext.asyncio import AsyncSession
from utils.utils import to_camel


class Model(pydantic.BaseModel):
    """Промежуточная модель pydantic'а для унифицирования конфигов и удобного администрирования."""

    class Config:  # noqa: D106
        alias_generator = to_camel
        allow_population_by_field_name = True

    # noinspection Pydantic
    @classmethod
    async def from_orm_async(cls: type["Model"], obj: Any, session: AsyncSession) -> "Model":
        """
        Преобразование ORM-модели в pydantic-модель асинхронно.

        При запросе ORM моделей, с помощью асинхронной сессии, невозможно
        подгрузить отношения в асинхронном контексте "on-demand" (lazy-load при запросе вложенной сущности).
        Также, могут возникнуть проблемы для полей, с ``server_default`` параметрами.

        В связи с вышеперечисленными проблемами есть 2 варианта сериализации ORM модели к Pydantic схеме:
         * использование классического (синхронного метода ``from_orm``) с предварительной подгрузкой всех сущностей
         * использование асинхронного ``from_orm_async``

        При первом сценарии, необходимо, чтобы все маппящиеся свойства были предварительно подгружены,
        для этого можно использовать метод ``session.refresh(<entity_var>, (*<field_name>))``
        (работает и для ``server_default`` и для вложенных сущностей)
        (не забывайте слить изменения в бд через ``session.flush``,
        иначе вы откатите изменения в ORM объектах).
        Либо при составлении запроса, указывать все вложенные сущности, с помощью метода запроса ``options``,
        например, ``select(User).options(joinedload(Role))``.

        **также, необходимо помнить, что для полей ORM модели с параметром ``server_default``, работает
        стандартное правило ``expire_on_commit``**
        (правда мы не используем ``session.commit()`` явно, за редкими исключениями, но всё же)
        """
        mapper = lambda sess, obj: cls.from_orm(obj)  # noqa: ARG005
        return await session.run_sync(mapper, obj)


class PydanticBoolCaster(pydantic.BaseModel):
    """Миксин для кастинга bool в строки."""

    @classmethod
    def __cast_bool_to_str(cls, values: dict) -> dict:  # noqa: ANN102
        for key, value in values.items():
            if isinstance(value, bool):
                values[key] = str(value).lower()
        return values

    def dict(self, bool_to_str: bool = False, **kwargs) -> dict:  # noqa: D102, ANN003
        values = super().dict(**kwargs)
        if bool_to_str:
            values = self.__cast_bool_to_str(values)
        return values


ListElement = TypeVar("ListElement", bound=Model)


class IdMixin(Model):
    """
    Миксин с полем Id для объектов.

    По своей сути крайне бесполезен, **однако** с помощью него можно задать порядок сортировки полей,
    сделав id первым полем в возвращаемых json объектах.

    Указывать первым справа, т.е. ``class YourModel(YourBaseModel, IdMixin)``
    """

    id: int

    class Config(Model.Config):  # noqa: D106, D106
        orm_mode = True


class UidMixin(Model):
    """Миксин со строковым (uuid) полем Id для объектов."""

    id: str

    class Config(Model.Config):  # noqa: D106
        orm_mode = True

    @pydantic.validator("id")
    def ensure_uuid(cls, value: str) -> str:  # noqa: D102, N805
        err = ValueError("Некорректный идентификатор")
        try:
            validated = uuid.UUID(value)
            if validated.version != 4:  # noqa: PLR2004
                raise err
        except ValueError as e:
            raise err from e

        return value


class ListModelBase(Model):
    """Базовая модель для формата выдачи списка объектов."""

    show_deleted: bool = False
    data: list[ListElement]
    sort_by: str = "id"
    descending: bool = False


class ListModel(ListModelBase):
    """Формат выдачи для всех списков объектов (multiple get)."""

    rows_per_page: Optional[int]
    page: Optional[int]
    rows_number: Optional[int]


class ListModelOffset(ListModelBase):
    """Формат выдачи для списков со смещением."""

    limit: Optional[int]
    offset: Optional[int]


class ErrorSchema(Model):
    """Формат данных для ошибок, возвращаемых сервисом."""

    detail: str


class CatalogElementCreate(Model):
    """Базовая модель для любого каталога."""

    name: str = pydantic.Field(..., max_length=256)
    description: str = pydantic.Field(..., max_length=1024)


class CatalogElementBare(CatalogElementCreate, IdMixin):
    """Базовая модель для выдачи любого каталога."""

    class Config(Model.Config):  # noqa: D106
        orm_mode = True


class StatusResponse(pydantic.BaseModel):
    """Формат ответа для запросов, в которых не требуется отдавать данные."""

    status: str = "ok"
    warning: Optional[str] = None
    warning_info: list[dict] = pydantic.Field(default_factory=list)
