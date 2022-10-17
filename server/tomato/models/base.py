import zoneinfo

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.html import format_html

from ..constants import HELP_DOCS_URL
from .user import User


NAME_MAX_LENGTH = 70
UTC = zoneinfo.ZoneInfo("UTC")


def greater_than_zero(value):
    if value <= 0:
        raise ValidationError("Value must be greater than 0")


class EligibleToAirQuerySet(models.QuerySet):
    def _get_currently_airing_Q(self, now=None):
        if now is None:
            now = timezone.now()
        return Q(enabled=True) & (Q(begin__isnull=True) | Q(begin__lte=now)) & (Q(end__isnull=True) | Q(end__gte=now))

    def eligible_to_air(self, now=None):
        return self.filter(self._get_currently_airing_Q(now))

    def not_eligible_to_air(self, now=None):
        return self.exclude(self._get_currently_airing_Q(now))


class EnabledBeginEndWeightMixin(models.Model):
    objects = EligibleToAirQuerySet.as_manager()

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
            "Date when eligibility for random selection <strong>ends</strong>. If specified, random selection is only"
            " eligible before this date. If left blank, its always eligible for random selection starting with begin"
            " air date."
        ),
    )
    weight = models.DecimalField(
        "weight",
        max_digits=6,
        decimal_places=2,
        default=1,
        validators=[greater_than_zero],
        help_text=format_html(
            "The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all"
            " others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and so on. See the"
            ' <a href="{}concepts#weight" target="_blank">docs for more information</a>.',
            HELP_DOCS_URL,
        ),
    )

    def is_eligible_to_air(self, now=None, with_reason=False):
        if now is None:
            now = timezone.now()
        if not self.enabled:
            return (False, "Not enabled") if with_reason else False
        if self.begin is not None and self.begin > now:
            return (False, "Before start air date") if with_reason else False
        if self.end is not None and self.end < now:
            return (False, "After end air date") if with_reason else False
        return (True, None) if with_reason else True

    def clean(self):
        super().clean()
        if self.begin and self.end and self.begin > self.end:
            raise ValidationError({"end": "End air date before begin air date."})

    def serialize(self):
        return {
            "enabled": self.enabled,
            "weight": round(float(self.weight), 2),
            "begin": self.begin,
            "end": self.end,
            **super().serialize(),
        }

    class Meta:
        abstract = True


class TomatoModelBase(models.Model):
    created_at = models.DateTimeField("created at", auto_now_add=True, db_index=True)
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
