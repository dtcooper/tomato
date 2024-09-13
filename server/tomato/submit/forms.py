from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(help_text="Enter your email address. You will be sent an email to verify it.")
