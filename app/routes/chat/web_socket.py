import asyncio
from enum import Enum
from typing import Dict

import fastapi
import jwt
from fastapi import Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from core import Config
from internal.chats import get_chat, send_message, get_message, all_message_chat

from utils.auth.passwwords import get_token
from utils.database_connection import db_async_session

web = fastapi.APIRouter()


class SocketType(Enum):
    UPDATE_USERS = "UPDATE_USERS"
    SEND_MESSAGE = "SEND_MESSAGE"


async def broadcast_events(data):
    body = data["body"]
    chat_id = body["chat"]["id"]

    if data["type"] == SocketType.SEND_MESSAGE.value:
        await Config.active_connections[body['recipient']].send_json(
            {"type": SocketType.SEND_MESSAGE.value, "body": {"message": body["message"]}})



@web.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()

    user_info = jwt.decode(data["Authorization"], Config.SECRET_KEY, Config.ALGORITHM)
    user_id = user_info["id"]
    Config.active_connections[user_id] = websocket
    print(f"Пользователь {user_id} подключён. Активные соединения: {Config.active_connections}")

    await websocket.send_json({"message": "привет"})

    try:
        while True:
            data = await websocket.receive_json()
            await broadcast_events(data)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print("Соединение разорвано", Config.active_connections[user_id])
        del Config.active_connections[user_id]


    except Exception as e:
        print(f"Ошибка у {user_id}: {str(e)}")
        print(e)
        del Config.active_connections[user_id]


@web.get("/active_connections")
def get_active_connections():
    return {"active": list(Config.active_connections.keys())}
