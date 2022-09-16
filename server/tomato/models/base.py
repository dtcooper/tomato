from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from .user import User


NAME_MAX_LENGTH = 75


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
            "<strong>Date when eligibility for random selection <u>begins</u>.</strong>  If specified, random"
            " selection is only eligible after this date. If left blank, its always eligible for random selection up"
            f" to end air date. [Timezone: {settings.TIME_ZONE}]"
        ),
    )
    end = models.DateTimeField(
        "end air date",
        null=True,
        blank=True,
        default=None,
        help_text=(
            "<strong>Date when eligibility for random selection <u>ends</u>.</strong> If specified, random selection"
            " is only eligible before this date. If left blank, its always eligible for random selection starting with"
            f" begin air date. [Timezone: {settings.TIME_ZONE}]"
        ),
    )
    weight = models.DecimalField(
        "random weight",
        max_digits=5,
        decimal_places=2,
        default=1,
        validators=[greater_than_zero],
        help_text=(
            "The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all"
            " others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and so on."
        ),
    )

    class Meta:
        abstract = True


class TomatoModelBase(models.Model):
    created_at = models.DateTimeField("created at", auto_now_add=True)
    created_by = models.ForeignKey(User, verbose_name="created by", on_delete=models.SET_NULL, null=True)
    name = models.CharField("name", max_length=NAME_MAX_LENGTH, db_index=True)

    class Meta:
        abstract = True
        ordering = (Lower("name"),)

    def __str__(self):
        return self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }
