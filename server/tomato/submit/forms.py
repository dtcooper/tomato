import random
import re

from django import forms
from django.core.cache import cache

from captcha.fields import CaptchaField
from constance import config
from django_file_form.forms import FileFormMixin, UploadedFileField

from ..models import Rotator
from ..tasks import process_asset
from .constants import SUBMIT_LOGIN_CAPTCHA_MAX_LENGTH, SUBMIT_LOGIN_CAPTCHA_MIN_LENGTH
from .models import Submission


class RotatorPickerField(forms.ChoiceField):
    def __init__(self, required=False, *args, **kwargs):
        choices = [("", "No default selected")]
        choices.extend(Rotator.objects.order_by("name").values_list("pk", "name"))
        super().__init__(choices=choices, required=required, *args, **kwargs)


class AlwaysClearableConstanceFileInput(forms.ClearableFileInput):
    template_name = "submit/admin/widgets/always_clearable_file_input.html"


LETTERS_ONLY_RE = re.compile(rf"^[a-z]{{{SUBMIT_LOGIN_CAPTCHA_MIN_LENGTH},{SUBMIT_LOGIN_CAPTCHA_MAX_LENGTH}}}$")
DICT_WORDS_PATH = "/usr/share/dict/words"
WORDS_CACHE_KEY = "tomato:words:cache"


def captcha_challenge():
    words = cache.get(WORDS_CACHE_KEY)
    if words is None:
        with open(DICT_WORDS_PATH, "r") as f:
            words = [w.strip() for w in f if LETTERS_ONLY_RE.match(w)]
        cache.set(WORDS_CACHE_KEY, words, timeout=60 * 60)
    word = random.choice(words).strip().upper()
    return (word, word)


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        help_text="Enter your email address to login.",
        widget=forms.TextInput(attrs={"placeholder": "user@example.com"}),
    )
    captcha = CaptchaField(
        label="CAPTCHA Test",
        help_text="Enter the word exactly as you see below. If you can't make it out, click refresh for a new word.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if getattr(config, "USER_SUBMIT_LOGIN_VIA_EMAIL", False):
            self.fields["email"].help_text += " You will be sent an email to confirm it"


class SubmissionForm(FileFormMixin, forms.ModelForm):
    def save(self, *args, **kwargs):
        submission = super().save(*args, **kwargs)
        process_asset(submission)
        return submission

    class Meta:
        model = Submission
        fields = ("name", "begin", "end")
        field_classes = {
            "file": UploadedFileField,
        }
