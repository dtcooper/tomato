import datetime
import hashlib
import random
import secrets
import string
from urllib.parse import urlparse

import base58

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.db import models
from django.db.models.functions import Lower

from .ffmpeg import ffprobe


NAME_MAX_LENGTH = 100
querystring_auth_storage = get_storage_class()(querystring_auth=True)


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

    def get_pw_hash(self, salt):
        to_hash = b"%d:%b:%b:%b" % (self.id, settings.SECRET_KEY.encode("utf-8"), salt, self.password.encode("utf-8"))
        return hashlib.sha256(to_hash).digest()

    def generate_auth_token(self):
        salt = ("".join(random.choice(self.POSSIBLE_SALT_CHARS) for _ in range(8))).encode("utf-8")
        raw_token = b"%b:%d:%b" % (salt, self.id, self.get_pw_hash(salt))
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
                    if secrets.compare_digest(pw_hash, user.get_pw_hash(salt)):
                        return user
        return None


class Rotator(models.Model):
    name = models.CharField(
        "rotator name",
        max_length=NAME_MAX_LENGTH,
        db_index=True,
        help_text="The name of this asset rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc.",
    )

    class Meta:
        db_table = "rotators"
        ordering = (Lower("name"),)

    def __str__(self):
        return self.name


class Asset(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        FAILED = 2, "Processing Failed"
        READY = 3, "Ready"

    created = models.DateTimeField("created at", auto_now_add=True)
    name = models.CharField(
        "name",
        max_length=NAME_MAX_LENGTH,
        blank=True,
        db_index=True,
        help_text=(
            "Optional name, if left unspecified, base it off the audio file's metadata and failing that its filename."
        ),
    )
    file = models.FileField("audio file", null=True, blank=False)
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)
    is_active = models.BooleanField(
        "enabled",
        default=True,
        help_text=(
            "Designates whether this audio asset is enabled. Unselect this to completely disable playing of this asset."
        ),
    )
    duration = models.DurationField(default=datetime.timedelta(0))
    rotators = models.ManyToManyField(
        Rotator,
        related_name="assets",
        blank=True,
        verbose_name="rotators",
        help_text="Rotators that this asset will be included in.",
    )

    def get_stripped_asset_url(self):
        return urlparse(self.file.url)._replace(query="", fragment="").geturl()

    def __str__(self):
        return self.name

    def clean(self):
        if self.file:
            url = querystring_auth_storage.url(self.file.file.obj.key)  # Get temporary upload url
            print(url)
            ffprobe_data = ffprobe(url)
            if not ffprobe_data:
                raise ValidationError({"file": "Invalid audio file"})

            self.duration = ffprobe_data.duration

            self.name = self.name.strip()
            if not self.name:
                self.name = ffprobe_data.title[:NAME_MAX_LENGTH].strip()

    class Meta:
        db_table = "assets"
        verbose_name = "audio asset"
        ordering = (Lower("name"),)
