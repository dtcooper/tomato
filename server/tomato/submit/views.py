import logging
import time
import secrets
import string

from django.core.mail import send_mail
from django.conf import settings
from django.http import Http404
from django.shortcuts import resolve_url as _resolve_url
from django.views.generic import FormView, RedirectView
from django.utils.text import camel_case_to_spaces
from django.contrib import messages

from constance import config

from ..constants import SUBMIT_TOKEN_MAX_AGE, SUBMIT_URL_PREFIX
from .forms import LoginForm


logger = logging.getLogger(__name__)

TOKEN_CHARS = string.ascii_letters + string.digits
TOKEN_LENGTH = 32
NAV_LINKS = (
    ("login", "Login"),
    ("logout", "Logout"),
)


class UserSubmissionMixin:
    title = "User Submission"
    template_name = None

    def setup(self, request, *args, **kwargs):
        self.submit_email = request.session.get("submit_email", None)
        self.submit_logged_in = request.session.get("submit_logged_in", False)
        super().setup(request, *args, **kwargs)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        else:
            basename = camel_case_to_spaces(self.__class__.__name__.removesuffix("View")).replace(" ", "-")
            return [f"tomato/submit/{basename}.html"]

    def resolve_url(self, view_name, *args, **kwargs):
        url = _resolve_url(f"user_submission_{view_name}", *args, **kwargs)
        if (
            settings.SUBMIT_ALT_DOMAIN_NAME is not None
            and self.request.get_host().lower() == settings.SUBMIT_ALT_DOMAIN_NAME.lower()
            and url.startswith(SUBMIT_URL_PREFIX)
        ):
            url = url.removeprefix(SUBMIT_URL_PREFIX)
        return url

    def message(self, message, level=messages.INFO):
        messages.add_message(self.request, level, message)

    def get_context_data(self, **kwargs):
        return {
            "title": self.title,
            "STATION_NAME": config.STATION_NAME,
            "email": self.submit_email,  # XXX needed?
            "is_logged_in": self.submit_logged_in,
            "nav_links": [(self.resolve_url(view), name) for view, name in NAV_LINKS],
            **super().get_context_data(**kwargs),
        }


class LoginView(UserSubmissionMixin, FormView):
    form_class = LoginForm
    title = "Audio Submission"

    def get_success_url(self):
        return self.resolve_url("login")

    @staticmethod
    def generate_token():
        return "".join(secrets.choice(TOKEN_CHARS) for _ in range(TOKEN_LENGTH))

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        token = self.generate_token()
        self.request.session.update({"submit_email": email, "submit_token": (token, time.time()), "submit_logged_in": False})
        logger.info(f"Sending token verification email to: {email}")

        link = self.request.build_absolute_uri(self.resolve_url("validate_token", token=token))
        send_mail("Test subject", f"Test message\n{link}", None, recipient_list=[email])
        self.message(f"An email has been sent to {email} with a link. Follow the link to log in.")
        return super().form_valid(form)


class LogoutView(UserSubmissionMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        self.request.session.pop("submit_logged_in", None)
        self.message("You have been logged out.")
        return self.resolve_url("login")


class ValidateView(UserSubmissionMixin, RedirectView):
    def get_redirect_url(self, token, *args, **kwargs):
        session_token, created_at = self.request.session.get("submit_token", (None, 0))
        if session_token is not None and secrets.compare_digest(token, session_token):
            if time.time() - created_at > SUBMIT_TOKEN_MAX_AGE:
                raise Http404("Token expired!")
            else:
                self.message("Your email address was successfully validated!", messages.SUCCESS)
                self.request.session["submit_logged_in"] = True
                del self.request.session["submit_token"]
                return self.resolve_url("login")
        else:
            raise Http404("Invalid token!")
