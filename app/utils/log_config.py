import logging
import warnings
from contextlib import contextmanager

import sentry_sdk
from fastapi import FastAPI


from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy import exc


def configure_logging(enable_additional_debug=True):
    """
    Отключает дебаг информацию для библиотек, при необходимости
    """
    while len(logging.root.handlers) > 0:
        logging.root.removeHandler(logging.root.handlers[-1])

    logging.getLogger("AdditionalDebug").info("enabled")
    if not enable_additional_debug:
        logging.getLogger("websockets.protocol:server").setLevel(logging.ERROR)
        logging.getLogger("websockets.protocol").setLevel(logging.ERROR)
        logging.getLogger("databases").setLevel(logging.ERROR)
        logging.getLogger("sqlalchemy.engine.base.Engine").setLevel(logging.ERROR)
        logging.getLogger("aiokafka.consumer.group_coordinator").setLevel(logging.ERROR)
        logging.getLogger("aiokafka.consumer.group_coordinator").setLevel(logging.ERROR)
        logging.getLogger("aiokafka.consumer.group_coordinator").setLevel(logging.ERROR)
        logging.getLogger("aiokafka.conn").setLevel(logging.ERROR)
        logging.getLogger("aiokafka.consumer.fetcher").setLevel(logging.ERROR)
        logging.getLogger("multipart.multipart").setLevel(logging.ERROR)

        warnings.simplefilter("ignore", category=exc.SAWarning)
    else:
        logging.getLogger("sqlalchemy.engine.base.Engine").setLevel(logging.INFO)


def set_logging(
    level=logging.DEBUG,
    enable_additional_debug: bool = True,
    sentry_url: str = None,
    environment: str = "TEST_LOCAL",
    app: FastAPI = None,
):
    """
    Устанавливает конфигурацию для логирования.

    Необходимо вызывать как можно раньше
    :param level: уровень выводимых логов
    """
    configure_logging(enable_additional_debug=enable_additional_debug)
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", force=True)

    if sentry_url:
        sentry_logging = LoggingIntegration(level=level, event_level=logging.ERROR)

        sentry_sdk.init(
            sentry_url,
            traces_sample_rate=1.0,
            environment=environment,
            integrations=[sentry_logging, SqlalchemyIntegration()],
        )


@contextmanager
def nested_transaction(name: str) -> sentry_sdk.hub.Transaction:
    """
    Контекстный менеджер для мониторинга производительности
    :param name: имя контекса для отслеживания
    :return:
    """
    transaction = sentry_sdk.Hub.current.scope.transaction
    if transaction is None:
        with sentry_sdk.start_transaction(name=name) as transaction:
            yield transaction
    else:
        with transaction.start_child(op=name):
            yield transaction
