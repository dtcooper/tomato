from django.db import models
from django.utils.safestring import mark_safe

from ..constants import COLORS, COLORS_DICT
from .base import TomatoModelBase
from .stopset import Stopset


class Rotator(TomatoModelBase):
    COLOR_CHOICES = tuple((c["name"], c["name"].replace("-", " ").title()) for c in COLORS)
    color = models.CharField(
        "Color",
        default=COLOR_CHOICES[0][0],
        max_length=20,
        choices=COLOR_CHOICES,
        help_text="Color that appears in the client for this rotator.",
    )
    is_single_play = models.BooleanField(
        "single play",
        default=False,
        help_text=(
            "Enable single play mode, which will cause the desktop app to allow playing a random asset from this"
            " rotator. (Standard and advanced mode only.)"
        ),
    )
    enabled = models.BooleanField(
        "enabled",
        default=True,
        help_text=mark_safe(
            "If unselected, rotator is <strong>completely disabled</strong> regardless of its inclusion in a stop set."
        ),
    )
    stopsets = models.ManyToManyField(
        Stopset,
        through="tomato.StopsetRotator",
        related_name="rotators",
        through_fields=("rotator", "stopset"),
        verbose_name="stop set",
    )

    def serialize(self):
        return {"color": self.color, "is_single_play": self.is_single_play, **super().serialize()}

    def get_color(self, content=False):
        return COLORS_DICT[self.color]["content" if content else "value"]

    class Meta(TomatoModelBase.Meta):
        db_table = "rotators"
        verbose_name = "rotator"


name_field = Rotator._meta.get_field("name")
name_field.help_text = "The name of this rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc."
del name_field
