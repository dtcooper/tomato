from django.db import models

from .base import BaseModel
from .stopset import StopSet


class Rotator(BaseModel):
    stopsets = models.ManyToManyField(
        StopSet,
        through="StopSetRotator",
        related_name="rotators",
        through_fields=("rotator", "stopset"),
        verbose_name="Stop Set",
    )

    class Meta:
        db_table = "rotators"


name_field = Rotator._meta.get_field("name")
name_field.verbose_name = "rotator name"
name_field.help_text = "The name of this asset rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc."
del name_field
