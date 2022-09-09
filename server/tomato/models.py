from django.db import models
from django.contrib.auth.models import AbstractUser


class TomatoUser(AbstractUser):
    is_staff = True
    first_name = None
    last_name = None

    def __init__(self, *args, **kwargs):
        if "is_staff" in kwargs:
            del kwargs["is_staff"]
        super().__init__(*args, **kwargs)
