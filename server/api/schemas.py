import enum

from schema import Optional, Or, Schema, Use


class ServerMessageTypes(enum.StrEnum):
    DB_CHANGE = "db-change"
    LOGOUT = "logout"


class UserMessageTypes(enum.StrEnum):
    ACK_ACTION = "ack-action"
    CLIENT_DATA = "client-data"
    SEND_LOG = "log"
    UNSUBSCRIBE = "unsubscribe"


class OutgoingUserMessageTypes(enum.StrEnum):
    ACKNOWLEDGE_LOG = "ack-log"
    DATA = "data"
    LOGOUT = "logout"
    NOTIFY = "notify"
    PLAY = "play"
    RELOAD_PLAYLIST = "reload-playlist"
    SUBSCRIBE = "subscribe"
    SWAP = "swap"
    UNSUBSCRIBE = "unsubscribe"


class AdminMessageTypes(enum.StrEnum):
    LOGOUT = "logout"
    NOTIFY = "notify"
    PLAY = "play"
    RELOAD_PLAYLIST = "reload-playlist"
    SUBSCRIBE = "subscribe"
    SWAP = "swap"
    UNSUBSCRIBE = "unsubscribe"


class OutgoingAdminMessageTypes(enum.StrEnum):
    ACK_ACTION = "ack-action"
    CLIENT_DATA = "client-data"
    LOGOUT = "logout"
    RELOAD_PLAYLIST = "reload-playlist"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    USER_CONNECTIONS = "user-connections"


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
    )
)
