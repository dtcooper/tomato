import datetime
import os

from django.core.exceptions import ValidationError
from django.db import models

from dirtyfields import DirtyFieldsMixin
from django_file_form.uploaded_file import UploadedTusFile

from ..ffmpeg import ffprobe
from .base import NAME_MAX_LENGTH, EnabledBeginEndWeightMixin, TomatoModelBase
from .rotator import Rotator


ERROR_DETAIL_LENGTH = 1024


class Asset(EnabledBeginEndWeightMixin, DirtyFieldsMixin, TomatoModelBase):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        FAILED = 2, "Processing failed"
        READY = 3, "Ready"

    name = models.CharField(
        "name",
        max_length=NAME_MAX_LENGTH,
        db_index=True,
        blank=True,
        help_text=(
            "Optional name, if left unspecified, we'll automatically base it off the audio file's metadata and failing"
            " that its filename."
        ),
    )
    file = models.FileField("audio file", null=True, blank=False)
    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.PENDING, help_text="All assets will be processed after uploading."
    )
    enabled = models.BooleanField(
        "enabled",
        default=True,
        help_text=(
            "Designates whether this asset is enabled. Unselect this to completely disable playing of this asset."
        ),
    )
    duration = models.DurationField(default=datetime.timedelta(0))
    rotators = models.ManyToManyField(
        Rotator,
        related_name="assets",
        blank=True,
        verbose_name="rotators",
        help_text="Rotators that this asset will be included in.",
    )
    error_detail = models.TextField(max_length=ERROR_DETAIL_LENGTH, blank=True)

    class Meta(TomatoModelBase.Meta):
        db_table = "assets"
        verbose_name = "audio asset"

    def serialize(self):
        return {
            "file": {"filename": self.file.name, "url": self.file.url},
            "duration": round(self.duration.total_seconds()),
            "rotators": [rotator.id for rotator in self.rotators.all()],
            **super().serialize(),
        }

    def clean(self):
        if self.file:
            if isinstance(self.file.file, UploadedTusFile):
                file_path = self.file.file.file.path
            else:
                file_path = self.file.path

            ffprobe_data = ffprobe(file_path)
            if not ffprobe_data:
                raise ValidationError({"file": "Invalid audio file"})

            self.duration = ffprobe_data.duration

            self.name = self.name.strip()
            if not self.name:
                if ffprobe_data.title:
                    self.name = ffprobe_data.title
                else:
                    self.name, _ = os.path.splitext(os.path.basename(self.file.name))
            self.name = self.name[: NAME_MAX_LENGTH - 1].strip() or "Untitled"


Asset.rotators.through.__str__ = lambda self: f"{self.asset.name} in {self.rotator.name}"
Asset.rotators.through._meta.verbose_name = "Asset in rotator relationship"
Asset.rotators.through._meta.verbose_name_plural = "Asset in rotator relationships"

created_by_field = Asset._meta.get_field("created_by")
created_by_field.verbose_name = "uploading user"
del created_by_field

created_at_field = Asset._meta.get_field("created_at")
created_at_field.verbose_name = "date uploaded"
del created_at_field
