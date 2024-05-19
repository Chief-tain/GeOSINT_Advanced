import inspect
import logging
import pathlib

import structlog
from sentry_sdk.integrations.logging import LoggingIntegration
from structlog_sentry import SentryProcessor

from shared import settings


logging.basicConfig(level=logging.NOTSET)
logging.getLogger('telethon').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('celery').setLevel(logging.WARNING)
logging.getLogger('aiormq').setLevel(logging.WARNING)
logging.getLogger('aio_pika').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('aiobotocore').setLevel(logging.WARNING)
logging.getLogger('aioboto3').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pymorphy3').setLevel(logging.WARNING)
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('charset_normalizer').setLevel(logging.WARNING)
logging.getLogger('thefuzz.process').setLevel(logging.ERROR)


def configure_sentry():
    if settings.SENTRY_ACCESS_KEY and settings.SENTRY_PROJECT_NUMBER:
        import sentry_sdk
        sentry_sdk.init(
            dsn=f"http://"  # NOQA
                f"{settings.SENTRY_ACCESS_KEY}@"
                f"{settings.SENTRY_HOST}:"
                f"{settings.SENTRY_PORT}/"
                f"{settings.SENTRY_PROJECT_NUMBER}",
            integrations=[
                LoggingIntegration(level=None, event_level=None),
            ],
        )


def remove_sentry_id(_, __, event_dict):
    try:
        event_dict.pop('sentry_id')
    except KeyError:
        pass

    return event_dict


STRUCTLOG_SHARED_PROCESSORS = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    SentryProcessor(
        tag_keys="__all__",
        level=logging._nameToLevel[settings.SENTRY_LOG_LEVEL.upper()],  # NOQA
        event_level=logging._nameToLevel[settings.SENTRY_EVENT_LEVEL.upper()],  # NOQA
    ),
    remove_sentry_id,
    structlog.contextvars.merge_contextvars,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt='iso'),
]


def configure_structlog():
    structlog.configure(
        processors=[
            *STRUCTLOG_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        cache_logger_on_first_use=True,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    handler = logging.StreamHandler()

    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=STRUCTLOG_SHARED_PROCESSORS,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(),
            ]
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(
    name: str = None,
):
    if not name:
        frame = inspect.stack()[1]
        name = pathlib.Path(frame.filename).name

    return structlog.get_logger(name)


configure_sentry()
configure_structlog()
