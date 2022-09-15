import hashlib
import random
import secrets
import string

import base58

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Salt can't contain ':' as it would break auth token splitting
    POSSIBLE_SALT_CHARS = (string.ascii_letters + string.digits + string.punctuation).replace(":", "")
    is_staff = True
    first_name = None
    last_name = None
    is_active = models.BooleanField(
        "account enabled",
        default=True,
        help_text="Designates whether this account is enabled. Unselect this instead of deleting an account.",
    )

    class Meta:
        db_table = "users"

    def __init__(self, *args, **kwargs):
        if "is_staff" in kwargs:
            del kwargs["is_staff"]
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
