from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email address", help_text="Enter your email address. You will be sent an email to verify it."
    )
