from django import forms

from django_file_form.forms import FileFormMixin, UploadedFileField

from ..models import Asset


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email address", help_text="Enter your email address. You will be sent an email to verify it."
    )


class SubmittedAssetForm(FileFormMixin, forms.ModelForm):
    file = UploadedFileField(label="Audio file")

    class Meta:
        model = Asset
        exclude = ("email", "created_at")
