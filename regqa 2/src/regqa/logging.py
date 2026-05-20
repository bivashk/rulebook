import datetime as dt
import json
import logging
import sys

# Attributes every LogRecord carries. Anything outside this set was attached by
# the caller via extra={...} and belongs in the JSON payload.
_STANDARD_ATTRS = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "taskName", "thread", "threadName",
    }
)

# Not a LogRecord attribute, but uvicorn attaches it to carry an ANSI-coloured
# copy of the same message. Forwarding it would duplicate every uvicorn line.
_IGNORED_ATTRS = frozenset({"color_message"})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": dt.datetime.fromtimestamp(record.created, tz=dt.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD_ATTRS or key in _IGNORED_ATTRS or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # uvicorn installs its own colourised handlers at import time. Left alone they
    # bypass the formatter above and the log stream stops being uniformly parseable.
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    # The access middleware in the api already logs every request with timing and
    # a request id, so uvicorn's own access line is a duplicate of strictly less
    # information.
    logging.getLogger("uvicorn.access").disabled = True
