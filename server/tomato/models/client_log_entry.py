import uuid

from django.db import models
from django.utils import timezone

from ..constants import CLIENT_LOG_ENTRY_TYPES
from .user import User


class ClientLogEntry(models.Model):
    class Type(models.TextChoices):
        INTERNAL_ERROR = "internal_error", "Internal client error"
        LOGGED_IN = "login", "Logged in or reconnected"
        LOGGED_OUT = "logout", "Logged out"
        OVERDUE = "overdue", "Playing of stop set overdue"
        PLAYED_ASSET = "played_asset", "Played an audio asset"
        PLAYED_STOPSET = "played_stopset", "Played an entire stop set"
        SKIPPED_ASSET = "skipped_asset", "Skipped (or played a partial) audio asset"
        SKIPPED_STOPSET = "skipped_stopset", "Skipped (or played a partial) stop set."
        WAITED = "waited", "Waited"
        UNSPECIFIED = "unspecified", "Unspecified"

    CATEGORIES = {
        Type.INTERNAL_ERROR.value: Type.INTERNAL_ERROR.value,
        Type.LOGGED_IN.value: "auth",
        Type.LOGGED_OUT.value: "auth",
        Type.PLAYED_ASSET.value: "asset",
        Type.PLAYED_STOPSET.value: "stopset",
        Type.SKIPPED_ASSET.value: "asset",
        Type.SKIPPED_STOPSET.value: "stopset",
        Type.OVERDUE.value: "wait",
        Type.UNSPECIFIED.value: Type.UNSPECIFIED.value,
        Type.WAITED.value: "wait",
    }

    if set(Type.values) != CLIENT_LOG_ENTRY_TYPES:
        raise Exception("Mismatch of client log entry types in constants.json")
    if set(CATEGORIES.keys()) != CLIENT_LOG_ENTRY_TYPES:
        raise Exception("Log entry type without a category found")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(
        default=timezone.now, db_index=True
    )  # Dont use auto_now_add since client provides
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, blank=True)
    type = models.CharField(
        max_length=max(len(value) for value in Type.values), choices=Type.choices, default=Type.UNSPECIFIED
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return (
            f"{self.created_by.username if self.created_by else 'unknown/deleted user'}:"
            f"{self.get_type_display().lower()} at {timezone.localtime(self.created_at.replace(microsecond=0))}"
        )

    def category(self):
        return self.CATEGORIES.get(self.type, "unspecified")

    class Meta:
        verbose_name = "client log entry"
        verbose_name_plural = "client log entries"
        db_table = "logs"
        ordering = ("-created_at", "-id")
