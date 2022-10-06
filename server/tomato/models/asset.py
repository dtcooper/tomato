import datetime
import hashlib
import os

from django.core.exceptions import ValidationError
from django.db import models

from dirtyfields import DirtyFieldsMixin
from django_file_form.uploaded_file import UploadedTusFile

from ..ffmpeg import ffprobe
from .base import NAME_MAX_LENGTH, EnabledBeginEndWeightMixin, TomatoModelBase
from .rotator import Rotator


class Asset(EnabledBeginEndWeightMixin, DirtyFieldsMixin, TomatoModelBase):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        READY = 2, "Ready"

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
    md5sum = models.BinaryField(max_length=16, null=True, default=None)
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

    class Meta(TomatoModelBase.Meta):
        db_table = "assets"
        verbose_name = "audio asset"
        ordering = ("-created_at",)

    def generate_peaks(self):
        if not self.file:
            return

    def generate_md5sum(self):
        md5sum = hashlib.md5()

        with self.file.open("rb") as file:
            while chunk := file.read(1024 * 128):
                md5sum.update(chunk)

        self.md5sum = md5sum.digest()

    def serialize(self):
        return {
            "file": {"filename": self.file.name, "url": self.file.url},
            "md5sum": self.md5sum.hex(),
            "duration": round(self.duration.total_seconds()),
            "rotators": [rotator.id for rotator in self.rotators.all()],
            **super().serialize(),
        }

    @property
    def file_path(self):
        return self.file.file.file.path if isinstance(self.file.file, UploadedTusFile) else self.file.path

    def clean(self):
        super().clean()
        if self.file:
            ffprobe_data = ffprobe(self.file_path)
            if not ffprobe_data:
                raise ValidationError({"file": "Error validating audio file"})

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
del created_by_field

created_at_field = Asset._meta.get_field("created_at")
created_at_field.verbose_name = "date uploaded"
del created_at_field
