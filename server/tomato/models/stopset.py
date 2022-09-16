from django.db import models

from .base import EnabledBeginEndWeightMixin, TomatoModelBase


class Stopset(EnabledBeginEndWeightMixin, TomatoModelBase):
    class Meta(TomatoModelBase.Meta):
        verbose_name = "stop set"
        db_table = "stopsets"


class StopsetRotator(models.Model):
    stopset = models.ForeignKey(Stopset, on_delete=models.CASCADE)
    rotator = models.ForeignKey("tomato.Rotator", on_delete=models.CASCADE, verbose_name="Rotator")

    def __str__(self):
        s = f"{self.rotator.name} in {self.stopset.name}"
        if self.id:
            num = StopsetRotator.objects.filter(stopset=self.stopset, id__lte=self.id).count()
            s = f"{num}. {s}"
        return s

    class Meta:
        db_table = "stopset_rotators"
        verbose_name = "rotator in stop set relationship"
        ordering = ("id",)
