import hashlib
import random
import secrets
import string

import base58

from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # Salt can't contain ':' as it would break auth token splitting
    POSSIBLE_SALT_CHARS = (string.ascii_letters + string.digits + string.punctuation).replace(":", "")
    is_staff = True
    first_name = None
    last_name = None
    email = EMAIL_FIELD = None
    REQUIRED_FIELDS = []
    REMOVED_FIELDS = ("is_staff", "first_name", "last_name", "email")

    class Meta:
        db_table = "users"

    def __init__(self, *args, **kwargs):
        for field in self.REMOVED_FIELDS:
            kwargs.pop(field, None)
        super().__init__(*args, **kwargs)

    def get_full_name(self):
        return ""  # avoids wonky display in templates/admin/object_history.html

    def _get_pw_hash(self, salt):
        to_hash = b"%d:%b:%b:%b" % (self.id, settings.SECRET_KEY.encode("utf-8"), salt, self.password.encode("utf-8"))
        return hashlib.sha256(to_hash).digest()

    def generate_auth_token(self):
        salt = ("".join(random.choice(self.POSSIBLE_SALT_CHARS) for _ in range(8))).encode("utf-8")
        raw_token = b"%b:%d:%b" % (salt, self.id, self._get_pw_hash(salt))
        return base58.b58encode(raw_token).decode("utf-8")

    @classmethod
    def get_user_for_auth_token(cls, auth_token):
        try:
            salt_user_id_pw_hash_split = base58.b58decode(auth_token).split(b":", 2)
        except ValueError:
            pass
        else:
            if len(salt_user_id_pw_hash_split) == 3:
                salt, user_id, pw_hash = salt_user_id_pw_hash_split
                try:
                    user = cls.objects.get(id=user_id, is_active=True)
                except cls.DoesNotExist:
                    pass
                else:
                    if secrets.compare_digest(pw_hash, user._get_pw_hash(salt)):
                        return user
        return None


is_active_field = User._meta.get_field("is_active")
is_active_field.verbose_name = "account enabled"
is_active_field.help_text = "Designates whether this account is enabled. Unselect this instead of deleting an account."
del is_active_field

is_superuser_field = User._meta.get_field("is_superuser")
is_superuser_field.verbose_name = "administrator account"
is_superuser_field.help_text = (
    "Designates that this user is an administrator and has all permissions. Only administrators can create and edit"
    " user accounts. "
)
del is_superuser_field

groups_field = User._meta.get_field("groups")
groups_field.help_text = (
    "The groups this user belongs to. If groups with overlapping permissions are selected, user will get the most"
    " possible permissions."
)
del groups_field
