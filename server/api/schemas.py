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


class AdminMessageTypes(enum.StrEnum):
    RELOAD_PLAYLIST = "reload-playlist"


class OutgoingAdminMessageTypes(enum.StrEnum):
    RELOAD_PLAYLIST = "reload-playlist"
    HELLO = "hello"


greeting_schema = Schema(
    Or(
        {
            "username": str,
            "password": str,
            "tomato": "radio-automation",
            "protocol_version": Use(int),
            Optional("admin_mode", default=False): Use(bool),
            Optional("method", default="text"): "text",
        },
        {
            "tomato": "radio-automation",
            "protocol_version": Use(int),
            Optional("admin_mode", default=False): Use(bool),
            "method": "session",
        },
        {
            "key": str,
            "user_id": int,
            "tomato": "radio-automation",
            "protocol_version": Use(int),
            "admin_mode": True,
            "method": "secret-key",
        },
    )
)
