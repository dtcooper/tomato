import hmac
import secrets
import struct

import base62

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import constant_time_compare, salted_hmac


class User(AbstractUser):
    ACCESS_TOKEN_ALGORITHM = "sha256"
    ACCESS_TOKEN_SALT_LENGTH = 8
    ACCESS_TOKEN_STRUCT = struct.Struct(
        f"!{ACCESS_TOKEN_SALT_LENGTH}sq{hmac.new(b'key', digestmod=ACCESS_TOKEN_ALGORITHM).digest_size}s"
    )

    enable_client_logs = models.BooleanField(
        "client logs entries enabled",
        default=True,
        help_text=(
            "Disable client logging for this account. In general you'll want to keep this enabled, but for test"
            " accounts you may not want to pollute the client logs."
        ),
    )
    is_staff = True
    first_name = None
    last_name = None
    email = EMAIL_FIELD = None
    REQUIRED_FIELDS = ()
    REMOVED_FIELDS = ("is_staff", "first_name", "last_name", "email")

    class Meta:
        db_table = "users"

    def __init__(self, *args, **kwargs):
        for field in self.REMOVED_FIELDS:
            kwargs.pop(field, None)
        super().__init__(*args, **kwargs)

    def get_full_name(self):
        return ""  # avoids wonky display in templates/admin/object_history.html

    def _get_access_token_hash(self, salt):
        return salted_hmac(salt, f"{self.id}:{self.password}", algorithm=self.ACCESS_TOKEN_ALGORITHM).digest()

    def generate_access_token(self):
        salt = secrets.token_bytes(self.ACCESS_TOKEN_SALT_LENGTH)
        raw_token = self.ACCESS_TOKEN_STRUCT.pack(salt, self.id, self._get_access_token_hash(salt))
        return base62.encodebytes(raw_token)

    @classmethod
    def validate_access_token(cls, auth_token):
        try:
            packed = base62.decodebytes(auth_token)
        except ValueError:
            pass
        else:
            if len(packed) == cls.ACCESS_TOKEN_STRUCT.size:
                salt, user_id, hash = cls.ACCESS_TOKEN_STRUCT.unpack(packed)
                try:
                    user = cls.objects.get(id=user_id, is_active=True)
                except cls.DoesNotExist:
                    pass
                else:
                    if user.has_usable_password() and constant_time_compare(hash, user._get_access_token_hash(salt)):
                        return user
        return None


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
