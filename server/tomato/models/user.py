from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from dirtyfields import DirtyFieldsMixin


class User(DirtyFieldsMixin, AbstractUser):
    created_at = models.DateTimeField("created at", default=timezone.localtime, db_index=True)
    created_by = models.ForeignKey("User", verbose_name="created by", on_delete=models.SET_NULL, null=True)
    enable_client_logs = models.BooleanField(
        "Write client logs",
        default=True,
        help_text=(
            "Use this to enable or disable client logging for this account. In general you'll want to keep this"
            " enabled, but for test accounts you may not want to pollute the client logs."
        ),
    )
    is_staff = True
    first_name = None
    last_name = None
    email = EMAIL_FIELD = None
    date_joined = None
    REQUIRED_FIELDS = ()
    REMOVED_FIELDS = ("is_staff", "first_name", "last_name", "email", "date_joined")

    class Meta:
        db_table = "users"

    def __init__(self, *args, **kwargs):
        for field in self.REMOVED_FIELDS:
            kwargs.pop(field, None)
        super().__init__(*args, **kwargs)

    def get_full_name(self):
        return ""  # avoids wonky display in templates/admin/object_history.html


is_active_field = User._meta.get_field("is_active")
is_active_field.verbose_name = "account enabled"
is_active_field.help_text = "Designates whether this account is enabled. Unselect this instead of deleting an account."
del is_active_field

is_superuser_field = User._meta.get_field("is_superuser")
is_superuser_field.verbose_name = "administrator account"
is_superuser_field.help_text = (
    "Designates that this user is an administrator and is implicitly in all groups. NOTE: Only administrators can"
    " create and edit user accounts. "
)
del is_superuser_field

groups_field = User._meta.get_field("groups")
groups_field.verbose_name = "permissions"
groups_field.help_text = "The permission groups this user belongs to."
del groups_field
