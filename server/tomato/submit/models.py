from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from tomato.models.asset import NAME_MAX_LENGTH, Asset, SubmissionAndAssetBase
from tomato.models.base import BeginEndMixin


class Submission(BeginEndMixin, SubmissionAndAssetBase):
    class SubmitStatus(models.IntegerChoices):
        TODO_0 = 0, "todo 0"
        TODO_1 = 1, "todo 1"
        TODO_2 = 2, "todo 2"

    created_at = models.DateTimeField("created at", default=timezone.localtime, db_index=True)
    created_by = models.EmailField("created by", db_index=True)
    name = models.CharField("name", max_length=NAME_MAX_LENGTH, unique=True, help_text="TODO name help text")
    submit_status = models.SmallIntegerField(
        choices=SubmitStatus.choices, default=SubmitStatus.TODO_0, help_text="TODO submit status help text."
    )

    def full_clean(self, *args, **kwargs):
        if Asset.objects.filter(name=self.name).exists():
            raise ValidationError(
                {"name": "An audio file already exists in our system with that name. Please choose another."}
            )
        super().full_clean(*args, **kwargs)

    class Meta:
        db_table = "submissions"
        verbose_name = "user submission"
        ordering = ("-created_at",)


Submission._meta.get_field("begin").help_text = "Custom begin date help text"
Submission._meta.get_field("end").help_text = "Custom end date help text"
