import datetime
import hashlib
import random
import secrets
import string
from urllib.parse import urlparse
import uuid

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


class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField("created at", auto_now_add=True)
    created_by = models.ForeignKey(
        User, verbose_name="created by", on_delete=models.SET_NULL, null=True, editable=False
    )
    name = models.CharField(
        "name",
        max_length=NAME_MAX_LENGTH,
        db_index=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = (Lower("name"),)


class Rotator(BaseModel):
    class Meta:
        db_table = "rotators"


rotator_name = Rotator._meta.get_field("name")
rotator_name.verbose_name = "rotator name"
rotator_name.help_text = "The name of this asset rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc."
del rotator_name


class Asset(BaseModel):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending processing"
        PROCESSING = 1, "Processing"
        FAILED = 2, "Processing Failed"
        READY = 3, "Ready"

    file = models.FileField("audio file", null=True, blank=False)
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)
    enabled = models.BooleanField(
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

    class Meta:
        db_table = "assets"
        verbose_name = "audio asset"
        ordering = (Lower("name"),)

    def serialize(self):
        return {
            "id": str(self.uuid),
            "url": self.file.url,
            "name": self.name,
            "duration": round(self.duration.total_seconds()),
            "rotators": list(self.rotators.values_list("uuid", flat=True)),
        }

    def get_stripped_asset_url(self):
        return urlparse(self.file.url)._replace(query="", fragment="").geturl()

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


asset_name = Asset._meta.get_field("name")
asset_name.blank = True
asset_name.help_text = (
    "Optional name, if left unspecified, base it off the audio file's metadata and failing that its filename."
)
del asset_name
