import zoneinfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .user import User


NAME_MAX_LENGTH = 75
UTC = zoneinfo.ZoneInfo("UTC")
ZULU_STRFTIME = "%Y-%m-%dT%H:%M:%SZ"


def greater_than_zero(value):
    if value <= 0:
        raise ValidationError("Value must be greater than 0")


class EnabledBeginEndWeightMixin(models.Model):
    enabled = models.BooleanField(
        "enabled",
        default=True,
        help_text="If unselected, entity is completely disabled regardless of begin and end air date.",
    )
    begin = models.DateTimeField(
        "begin air date",
        null=True,
        blank=True,
        default=None,
        help_text=(
            "Date when eligibility for random selection <strong>begins</strong>. If specified, random selection is only"
            " eligible after this date. If left blank, its always eligible for random selection up to end air date."
        ),
    )
    end = models.DateTimeField(
        "end air date",
        null=True,
        blank=True,
        default=None,
        help_text=(
            f"Date when eligibility for random selection <strong>ends</strong>. If specified, random selection is only"
            f" eligible before this date. If left blank, its always eligible for random selection starting with begin"
            f" air date."
        ),
    )
    weight = models.DecimalField(
        "weight",
        max_digits=5,
        decimal_places=2,
        default=1,
        validators=[greater_than_zero],
        help_text=(
            "The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all"
            " others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and so on."
        ),
    )

    def serialize(self):
        return {
            "enabled": self.enabled,
            "weight": round(float(self.weight), 2),
            "begin": self.begin and self.begin.astimezone(UTC).strftime(ZULU_STRFTIME),
            "end": self.end and self.end.astimezone(UTC).strftime(ZULU_STRFTIME),
            **super().serialize(),
        }

    class Meta:
        abstract = True


class TomatoModelBase(models.Model):
    created_at = models.DateTimeField("created at", auto_now_add=True)
    created_by = models.ForeignKey(User, verbose_name="created by", on_delete=models.SET_NULL, null=True)
    name = models.CharField("name", max_length=NAME_MAX_LENGTH, unique=True)

    class Meta:
        abstract = True
        ordering = ("name",)

    def __str__(self):
        return self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }
