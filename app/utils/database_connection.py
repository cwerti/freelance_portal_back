from core.config import Config

from utils.factory import async_session_factory
from utils.json_serialization import dumps

engine_params = dict(json_serializer=dumps)

db_async_session, db_async_session_manager, async_engine = async_session_factory(
    Config.async_db_conn_str, **engine_params, echo=True
)
