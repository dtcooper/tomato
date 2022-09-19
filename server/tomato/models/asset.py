import datetime
import os
from urllib.parse import unquote, urlparse

from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.db import models

from ..ffmpeg import ffprobe
from .base import NAME_MAX_LENGTH, EnabledBeginEndWeightMixin, TomatoModelBase
from .rotator import Rotator


querystring_auth_storage = get_storage_class()(querystring_auth=True)
ERROR_DETAIL_LENGTH = 1024


class Asset(EnabledBeginEndWeightMixin, TomatoModelBase):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        FAILED = 2, "Processing failed"
        PROCESSED = 3, "Ready (processed)"

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
            "url": self.file.url,
            "duration": round(self.duration.total_seconds()),
            "rotators": [rotator.id for rotator in self.rotators.all()],
            **super().serialize(),
        }

    def get_stripped_asset_url(self):
        return urlparse(self.file.url)._replace(query="", fragment="").geturl()

    def clean(self):
        if self.file:
            url = querystring_auth_storage.url(self.file.file.obj.key)  # Get temporary upload url
            ffprobe_data = ffprobe(url)
            if not ffprobe_data:
                raise ValidationError({"file": "Invalid audio file"})

            self.duration = ffprobe_data.duration

            self.name = self.name.strip()
            if not self.name:
                if ffprobe_data.title:
                    self.name = ffprobe_data.title
                else:
                    title_from_filename, _ = os.path.splitext(os.path.basename(urlparse(url).path))
                    self.name = unquote(title_from_filename)[:NAME_MAX_LENGTH].strip()


Asset.rotators.through.__str__ = lambda self: f"{self.asset.name} in {self.rotator.name}"
Asset.rotators.through._meta.verbose_name = "Asset in rotator relationship"
Asset.rotators.through._meta.verbose_name_plural = "Asset in rotator relationships"

created_by_field = Asset._meta.get_field("created_by")
created_by_field.verbose_name = "uploading user"
del created_by_field

created_at_field = Asset._meta.get_field("created_at")
created_at_field.verbose_name = "date uploaded"
del created_at_field
