from django.db import models
from django.db.models.functions import Lower

from .user import User


NAME_MAX_LENGTH = 75


class BaseModel(models.Model):
    created_at = models.DateTimeField("created at", auto_now_add=True)
    created_by = models.ForeignKey(
        User, verbose_name="created by", on_delete=models.SET_NULL, null=True, editable=False
    )
    name = models.CharField(
        "name",
        max_length=NAME_MAX_LENGTH,
        db_index=True,
    )

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
