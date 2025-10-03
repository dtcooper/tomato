import datetime
import hashlib
import itertools
import logging
from pathlib import Path
import random
import string

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from constance import config

from ..utils import listdir_recursive
from .base import (
    FILE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    AudioFileField,
    EligibleToAirQuerySet,
    EnabledBeginEndWeightMixin,
    TomatoModelBase,
)
from .rotator import Rotator


logger = logging.getLogger(__name__)


class AssetEligibleToAirQuerySet(EligibleToAirQuerySet):
    def _get_currently_airing_Q(self, now=None):
        return models.Q(status=Asset.Status.READY) & super()._get_currently_airing_Q(now)


def generate_random_asset_filename(original_filename):
    stem = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"{stem}{Path(original_filename).suffix}"


def asset_upload_to(instance, filename):
    # Should work the same as in prefill_sample_data.py
    return generate_random_asset_filename(filename)


class AssetBase(TomatoModelBase):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        READY = 2, "Ready"

    file = AudioFileField("audio file", upload_to=asset_upload_to)
    # Original filename WITHOUT a suffix (stem only)
    original_filename = models.CharField(max_length=FILE_MAX_LENGTH)
    pre_process_md5sum = models.BinaryField(max_length=16, null=True, default=None)
    md5sum = models.BinaryField(max_length=16, null=True, default=None)
    filesize = models.BigIntegerField(default=-1)
    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.PENDING, help_text="All assets will be processed after uploading."
    )
    duration = models.DurationField(default=datetime.timedelta(0))
    comment = models.TextField(help_text="Any private comments about a particular asset", blank=True)

    SERIALIZE_FIELDS_TO_IGNORE = {
        "pre_process_md5sum",
        "md5sum",
        "status",
        "file",
        "duration",
    } | TomatoModelBase.SERIALIZE_FIELDS_TO_IGNORE

    class Meta:
        abstract = True

    def serialize(self):
        return {
            **super().serialize(),
            "duration": round(self.duration.total_seconds()),
            "md5sum": self.md5sum.hex(),
            "file": self.file.name,
            "url": self.file.url,
        }

    def full_clean(self, force_check_against_md5sum=None, *args, **kwargs):
        super().full_clean(*args, **kwargs)
        if self.file and (force_check_against_md5sum is not None or "file" in self.get_dirty_fields()):
            if config.PREVENT_DUPLICATE_ASSETS:
                md5sum = force_check_against_md5sum or self.generate_md5sum()
                querysets = {
                    Asset: Asset.objects.filter(pre_process_md5sum=md5sum),
                    AssetAlternate: AssetAlternate.objects.filter(pre_process_md5sum=md5sum),
                }
                if self.id is not None:
                    querysets[self._meta.model] = querysets[self._meta.model].exclude(id=self.id)

                duplicates = []
                for queryset in querysets.values():
                    for duplicate in queryset:
                        meta = duplicate._meta
                        duplicates.append((
                            reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=(duplicate.id,)),
                            duplicate.name,
                        ))
                if duplicates:
                    duplicates_html = format_html_join(", ", '<a href="{}">{}</a>', duplicates)
                    raise ValidationError({
                        "__all__": format_html(
                            "An audio asset already exists with this audio file. Rejecting duplicate. You can turn this"
                            " feature off with setting <code>PREVENT_DUPLICATES</code>. Existing: {}",
                            duplicates_html,
                        ),
                        "file": format_html("A duplicate of this file already exists. Existing: {}", duplicates_html),
                    })

    def pre_save_normalize_hook(self):
        pass

    def save(self, dont_overwrite_original_filename=False, *args, **kwargs):
        if not dont_overwrite_original_filename and "file" in self.get_dirty_fields():
            self.original_filename = Path(self.file.name).with_suffix("").name
        self.pre_save_normalize_hook()  # Way to clean up `self.name`
        super().save(*args, **kwargs)

    def generate_md5sum(self):
        md5sum = hashlib.md5()

        with open(self.file.real_path, "rb") as file:
            while chunk := file.read(1024 * 128):
                md5sum.update(chunk)

        return md5sum.digest()

    @property
    def filename(self):
        return f"{self.original_filename}{Path(self.file.name).suffix}"


class Asset(EnabledBeginEndWeightMixin, AssetBase):
    objects = AssetEligibleToAirQuerySet.as_manager()

    name = models.CharField(
        "name",
        max_length=NAME_MAX_LENGTH,
        db_index=True,
        blank=True,
        help_text="Optional name, if left empty, we'll automatically choose one for you.",
    )
    enabled = models.BooleanField(
        "enabled",
        default=True,
        help_text=(
            "Designates whether this asset is enabled. Unselect this to completely disable playing of this asset."
        ),
    )
    rotators = models.ManyToManyField(
        Rotator,
        related_name="assets",
        blank=True,
        verbose_name="rotators",
        help_text="Rotators that this asset will be included in.",
        db_table="asset_rotators",
    )
    archived = models.BooleanField(
        "archived",
        default=False,
        help_text="Archived models will not show in the desktop client. Think of archive as 'soft delete'.",
    )

    class Meta(TomatoModelBase.Meta):
        db_table = "assets"
        verbose_name = "audio asset"
        ordering = ("-created_at",)
        permissions = [
            ("configure_live_clients", "Can configure live desktop clients"),
            ("export_import", "Can manage (import/export/delete all) asset data"),
        ]

    def __str__(self):
        return f"{self.name}{' (archived)' if self.archived else ''}"

    def pre_save_normalize_hook(self):
        self.name = (
            self.name[:NAME_MAX_LENGTH].strip() or self.original_filename[:NAME_MAX_LENGTH].strip() or "Untitled"
        )

    def is_eligible_to_air(self, now=None, with_reason=False):
        if self.status != self.Status.READY:
            return (False, "Processing") if with_reason else False
        response = super().is_eligible_to_air(now, with_reason)
        if self.archived:
            if with_reason:
                response = (False, "Archived" if response[1] is None else f"Archived and {response[1].lower()}")
            else:
                response = False
        return response

    def serialize(self, alternates_already_filtered_by_prefetch=False):
        alternates_qs = self.alternates.all()
        if not alternates_already_filtered_by_prefetch:
            alternates_qs = alternates_qs.filter(status=AssetAlternate.Status.READY).order_by("id")

        return {
            **super().serialize(),
            "alternates": [alternate.serialize() for alternate in alternates_qs],
            "rotators": [rotator.id for rotator in self.rotators.all()],
        }

    def clean(self):
        super().clean()
        if not self.name.strip():
            self.name = self.original_filename


class AssetRotatorsProxy(Asset.rotators.through):
    class Meta:
        proxy = True


Asset.rotators.through.__str__ = lambda self: f"{self.asset.name} in {self.rotator.name}"
Asset.rotators.through._meta.verbose_name = "Asset in rotator relationship"
Asset.rotators.through._meta.verbose_name_plural = "Asset in rotator relationships"


class AssetAlternate(AssetBase):
    _num_before = None
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="alternates", verbose_name="alternate for asset"
    )

    # Property existing means there's no name field on this model
    @property
    def name(self):
        return f"Alternate #{self.num_before} for {self.asset}"

    @property
    def num_before(self):
        if self.id is None:
            return -1
        if self._num_before is None:
            # Cache miss!
            self._num_before = AssetAlternate.objects.filter(asset_id=self.asset_id, id__lt=self.id).count() + 1
        return self._num_before

    @classmethod
    def annotate_queryset_with_num_before(cls, qs=None):
        if qs is None:
            qs = cls.objects.all()
        num_before_subquery = (
            cls.objects.filter(asset_id=OuterRef("asset_id"), id__lt=OuterRef("id"))
            .order_by()
            .values("asset")
            .annotate(num=Count("*"))
            .values("num")
        )
        return qs.annotate(_num_before=Coalesce(Subquery(num_before_subquery), 0) + 1)

    class Meta(TomatoModelBase.Meta):
        db_table = "asset_alternates"
        ordering = ("id",)
        verbose_name = "audio asset alternate"
        verbose_name_plural = "asset alternates"


for model_class in (Asset, AssetAlternate):
    created_at_field = model_class._meta.get_field("created_at")
    created_at_field.verbose_name = "date uploaded"
    del created_at_field
del model_class


class SavedAssetFile(models.Model):
    file = models.FileField(max_length=FILE_MAX_LENGTH)
    original_filename = models.CharField(max_length=FILE_MAX_LENGTH)

    @property
    def filename(self):
        return f"{self.original_filename}{Path(self.file.name).suffix}"

    @classmethod
    def cleanup_unreferenced_files(cls):
        model_file_fields = []

        # Cleanup untracked files below

        # Figure out what models have file fields
        for model_cls in apps.get_models():
            if model_cls is not cls:
                model_fields = model_cls._meta.get_fields()
                for field in model_fields:
                    if isinstance(field, models.FileField):
                        model_file_fields.append((model_cls, field.name))

        # Build our sets of files in the DB
        recorded_db_files = set(cls.objects.values_list("file", flat=True))
        all_db_files = (
            set(
                itertools.chain.from_iterable(
                    model_cls.objects.values_list(file_field, flat=True) for model_cls, file_field in model_file_fields
                )
            )
            | recorded_db_files
        )
        db_files_that_should_be_recorded = (
            set(
                itertools.chain.from_iterable(
                    model_cls.objects.values_list("file", flat=True) for model_cls in (Asset, AssetAlternate)
                )
            )
            - recorded_db_files
        )

        # Create missing SavedAssetFiles (potentially unrecorded because of older version of tomato)
        for file in db_files_that_should_be_recorded:
            for model_cls, file_field in model_file_fields:
                try:
                    obj = model_cls.objects.get(**{file_field: file})
                except ObjectDoesNotExist:
                    pass
                else:
                    break
            else:
                raise Exception("Should not have gotten here!")

            cls.objects.create(file=obj.file, original_filename=obj.original_filename)

        if db_files_that_should_be_recorded:
            logger.warning(f"Now tracking {len(db_files_that_should_be_recorded)} files that should have been tracked")

        all_files_on_disk = set(listdir_recursive(settings.MEDIA_ROOT))

        logger.info(f"Tracking {len(all_db_files)} files, found {len(all_files_on_disk)} files on disk")
        files_to_be_deleted = all_files_on_disk - all_db_files
        media_root = Path(settings.MEDIA_ROOT)
        for file_to_be_deleted in files_to_be_deleted:
            file = media_root / file_to_be_deleted
            file.unlink()
        logger.info(f"Deleted {len(files_to_be_deleted)} untracked files")

    def __str__(self):
        return self.filename
