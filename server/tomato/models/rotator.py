from django.db import models

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
        help_text="Color that appears in the playout software for assets in this rotator.",
    )
    stopsets = models.ManyToManyField(
        Stopset,
        through="tomato.StopsetRotator",
        related_name="rotators",
        through_fields=("rotator", "stopset"),
        verbose_name="stop set",
    )

    def serialize(self):
        return {"color": self.color, **super().serialize()}

    def get_color(self, content=False):
        return COLORS_DICT[self.color]["content" if content else "value"]

    class Meta(TomatoModelBase.Meta):
        db_table = "rotators"
        verbose_name = "rotator"


name_field = Rotator._meta.get_field("name")
name_field.help_text = "The name of this rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc."
del name_field
