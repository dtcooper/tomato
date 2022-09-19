import uuid

from django.db import models
from django.utils import timezone

from ..constants import CLIENT_LOG_ENTRY_TYPES
from .user import User


class ClientLogEntry(models.Model):
    class Type(models.TextChoices):
        PLAYED_ASSET = "played_asset", "Played an audio asset"
        PLAYED_PARTIAL_STOPSET = "played_part_stopset", "Played a partial stop set"
        PLAYED_STOPSET = "played_stopset", "Played an entire stop set"
        SKIPPED_ASSET = "skipped_asset", "Skipped playing an audio asset"
        SKIPPED_STOPSET = "skipped_stopset", "Skipped playing an entire stop set"
        WAITED = "waited", "Waited"

    if set(Type.values) != set(CLIENT_LOG_ENTRY_TYPES):
        raise Exception("Mismatch of client log entry types in constants.json")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(
        default=timezone.now, db_index=True
    )  # Dont use auto_now_add since client provides
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, blank=True)
    type = models.CharField(max_length=max(len(value) for value in Type.values), choices=Type.choices)
    description = models.TextField(blank=True)

    def __str__(self):
        return (
            f"{self.created_by.username if self.created_by else 'unknown user'} {self.get_type_display().lower()} at"
            f" {timezone.localtime(self.created_at)}"
        )

    class Meta:
        verbose_name = "log entry"
        verbose_name_plural = "log entries"
        db_table = "logs"
        ordering = ("-created_at",)
