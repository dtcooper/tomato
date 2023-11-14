import enum

from schema import Optional, Or, Schema, Use


class ServerMessageTypes(enum.StrEnum):
    DB_CHANGE = "db-change"
    DB_CHANGES = "db-changes"  # de-duped
    DB_CHANGE_FORCE_UPDATE = "db-changes-force"  # forced
    RELOAD_PLAYLIST = "reload-playlist"


class UserMessageTypes(enum.StrEnum):
    SEND_LOG = "log"


class OutgoingUserMessageTypes(enum.StrEnum):
    DATA = "data"
    ACKNOWLEDGE_LOG = "ack-log"
    RELOAD_PLAYLIST = "reload-playlist"
    BROADCAST_NOTICE = "broadcast"


class AdminMessageTypes(enum.StrEnum):
    pass


class OutgoingAdminMessageTypes(enum.StrEnum):
    pass


class DjangoServerMessageTypes(enum.StrEnum):
    BROADCAST_NOTICE = "broadcast"


class OutgoingDjangoServerMessageTypes(enum.StrEnum):
    RESPONSE = "response"


greeting_schema = Schema(
    Or(
        {
            "tomato": "radio-automation",
            "protocol_version": Use(int),
            "username": str,
            "password": str,
            Optional("mode", default="user"): Or("user", "admin"),
            Optional("method", default="text"): "text",
        },
        {
            "tomato": "radio-automation",
            "protocol_version": Use(int),
            Optional("mode", default="user"): Or("user", "admin"),
            "method": "session",
        },
        {
            "tomato": "radio-automation",
            "protocol_version": Use(int),
            "secret_key": str,
            "mode": "server",
            "method": "secret-key",
        },
    )
)
