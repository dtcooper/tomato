import datetime
import hashlib
from pathlib import Path
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe

from constance import config
from dirtyfields import DirtyFieldsMixin

from .base import NAME_MAX_LENGTH, AudioFileField, EligibleToAirQuerySet, EnabledBeginEndWeightMixin, TomatoModelBase
from .rotator import Rotator


class AssetEligibleToAirQuerySet(EligibleToAirQuerySet):
    def _get_currently_airing_Q(self, now=None):
        return models.Q(status=Asset.Status.READY) & super()._get_currently_airing_Q(now)


TIMESTAMP_PREFIX = re.compile(r"^\d{15}_")


def asset_upload_to(instance, filename):
    # Prefix with current time to avoid dupes, scrubbing last prefix to avoid massive filenames
    filename = TIMESTAMP_PREFIX.sub("", str(filename))
    return f"{timezone.now().strftime('%y%m%d%H%M%S%f')[:-3]}_{filename}"


class Asset(EnabledBeginEndWeightMixin, DirtyFieldsMixin, TomatoModelBase):
    objects = AssetEligibleToAirQuerySet.as_manager()

    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        READY = 2, "Ready"

    name = models.CharField(
        "name",
        max_length=NAME_MAX_LENGTH,
        db_index=True,
        blank=True,
        help_text="Optional name, if left empty, we'll automatically choose one for you.",
    )
    file = AudioFileField("audio file", upload_to=asset_upload_to)
    pre_process_md5sum = models.BinaryField(max_length=16, null=True, default=None)
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
        permissions = [("immediate_play_asset", "Can immediately play audio assets")]

    def save(self, *args, **kwargs):
        self.name = self.name[:NAME_MAX_LENGTH].strip() or "Untitled"
        super().save(*args, **kwargs)

    def full_clean(self, *args, **kwargs):
        super().full_clean(*args, **kwargs)
        if config.PREVENT_DUPLICATES and self.file and "file" in self.get_dirty_fields():
            qs = Asset.objects.filter(pre_process_md5sum=self.generate_md5sum())
            if self.id is not None:
                qs = qs.exclude(id=self.id)
            if qs.exists():
                raise ValidationError(
                    {
                        "__all__": mark_safe(
                            "An audio asset already exists with this audio file. Rejecting duplicate. You can turn this"
                            " feature off with setting <code>PREVENT_DUPLICATES</code>."
                        ),
                        "file": "A duplicate of this file already exists.",
                    }
                )

    def is_eligible_to_air(self, now=None, with_reason=False):
        if self.status != self.Status.READY:
            return (False, "Processing") if with_reason else False
        return super().is_eligible_to_air(now, with_reason)

    def generate_md5sum(self):
        md5sum = hashlib.md5()

        with open(self.file_path, "rb") as file:
            while chunk := file.read(1024 * 128):
                md5sum.update(chunk)

        return md5sum.digest()

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
        return self.file.real_path

    def clean(self):
        super().clean()
        if not self.name.strip():
            self.name = Path(self.file.name).stem


Asset.rotators.through.__str__ = lambda self: f"{self.asset.name} in {self.rotator.name}"
Asset.rotators.through._meta.verbose_name = "Asset in rotator relationship"
Asset.rotators.through._meta.verbose_name_plural = "Asset in rotator relationships"

created_by_field = Asset._meta.get_field("created_by")
del created_by_field

created_at_field = Asset._meta.get_field("created_at")
created_at_field.verbose_name = "date uploaded"
del created_at_field
