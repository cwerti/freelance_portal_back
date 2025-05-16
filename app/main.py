import pathlib

import fastapi

from starlette.middleware.cors import CORSMiddleware

from typing import TYPE_CHECKING

from routes.account import auth
from routes.chat.chat_associations import associations
from routes.chat.chats import chats
from routes.chat.web_socket import web
from routes.reviews import reviews
from routes.orders import orders
from routes.chat.messages import message
from routes.bids import bids

from routes.files import files
from utils.log_config import set_logging

from core.config import Config
from routes.exceptions import add_exception_handlers

# if TYPE_CHECKING:
#     from utils.auth.blocked_jwt import BlockedJWTStorage
#     from utils.auth.user_info import UserInfoFetcher


description = """
### Права доступа к сущностям

Для каждой сущности предусмотрен определённый набор прав, которые, в зависимости от логики, могут назначаться различному
набору ролей. Также, помимо основного набора прав, ограничения могут быть выставлены непосредственно на уровне определённых ролей.

### Тестирование
Для тестирования запросов к API существует служебный токен (обладающий правами суперадминистратора), который можно сконфигурировать в
конфиг-переменной ``test_token``
"""

tags_metadata = [
    {"name": "User", "description": "Роуты для работы с пользователями"},
    {"name": "Files", "description": "Роуты для работы с файлами"},
    {"name": "Chats", "description": "Роуты для работы с чатами"},
    {"name": "Websockets","description": "Роуты для работы с веб-сокетами"}
]

app = fastapi.FastAPI(
    title="Портал фриланс биржа",
    description=description,
    version="0.0.1",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "docExpansion": "none",
        "displayRequestDuration": "true",
        "syntaxHighlight.theme": "obsidian",
        "tryItOutEnabled": "true",
        "requestSnippetsEnabled": "true",
    },
)

set_logging(
    level=Config.log_level,
    enable_additional_debug=Config.additional_debug,
    app=app,
)

default_errors = {
    401: {"description": "Unauthorized"},
    403: {"description": "No permission"},
    404: {"description": "Object not found"},
    409: {"description": "Collision occurred. Entity already exists"},
    410: {"description": "Already Expired"},
}

add_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    allow_credentials=True,
)


# @app.on_event("shutdown")
# async def shutdown():
#     if user_fetcher := getattr(app.state, "user_fetcher", None):
#         user_fetcher: UserInfoFetcher
#         await user_fetcher.close()
#
#     if blocked_jwt := getattr(app.state, "blocked_jwt", None):
#         blocked_jwt: BlockedJWTStorage
#         await blocked_jwt.close()

@app.get("/")
async def home():
    return {"data": "Hello World"}


app.include_router(auth, prefix="/user", tags=["User"])
app.include_router(files, prefix="/files", tags=["Files"])
app.include_router(chats, prefix="/chats", tags=["Chats"])
app.include_router(associations, prefix="/chats", tags=["Chats"])
app.include_router(message, prefix="/chats", tags=["Chats"])

app.include_router(reviews, prefix="/reviews", tags=["reviews"])
app.include_router(orders, prefix="/orders", tags=["orders"])
app.include_router(bids, prefix="/bids", tags=["bids"])
app.include_router(web, tags=["Websockets"])

