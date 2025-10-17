import datetime
import secrets
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import resolve_url as _resolve_url
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import camel_case_to_spaces
from django.views import generic

from constance import config

from .constants import SUBMIT_LOGIN_CAPTCHA_MAX_LENGTH, SUBMIT_TOKEN_MAX_AGE, SUBMIT_URL_PREFIX
from .forms import LoginForm, SubmissionForm
from .models import Submission


def resolve_url(request, url_name, *args, _external=False, **kwargs):
    url = _resolve_url(f"submit:{url_name}", *args, **kwargs)
    if (
        settings.USER_SUBMIT_ALT_DOMAIN_NAME is not None
        and request.get_host().lower() == settings.USER_SUBMIT_ALT_DOMAIN_NAME.lower()
        and url.startswith(f"/{SUBMIT_URL_PREFIX}/")
    ):
        url = url.removeprefix(f"/{SUBMIT_URL_PREFIX}")
    if _external:
        url = request.build_absolute_uri(url)
    return url


class SubmitMixin:
    title = "User Audio Submissions"
    template_name = None

    TOKEN_CHARS = string.ascii_letters + string.digits
    TOKEN_LENGTH = 32

    def generate_token(self):
        return "".join(secrets.choice(self.TOKEN_CHARS) for _ in range(self.TOKEN_LENGTH))

    def resolve_url(self, url_name, *args, **kwargs):
        return resolve_url(self.request, url_name, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not config.ENABLE_USER_SUBMIT:
            raise Http404("User submissions disabled")
        return super().dispatch(request, *kwargs, **kwargs)

    def get_success_url(self):
        success_url = super().get_success_url()
        return self.resolve_url(success_url)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        else:
            basename = camel_case_to_spaces(self.__class__.__name__.removesuffix("View")).replace(" ", "-")
            return [f"submit/{basename}.html"]

    def send_verify_email(self, email):
        token = self.generate_token()
        self.request.session["token"] = (
            email,
            token,
            timezone.now() + datetime.timedelta(seconds=SUBMIT_TOKEN_MAX_AGE),
        )
        link = self.resolve_url("verify", token=token, _external=True)
        message = render_to_string("submit/login_email.txt", {"STATION_NAME": config.STATION_NAME, "LINK": link})
        send_mail("Test Subject", message.strip(), from_email=None, recipient_list=[email])
        info_msg = format_html("A login email has been dispatched to <em>{}</em>.", email)
        if settings.DEBUG:
            info_msg = format_html('{} <em>(DEBUG: <a href="{}">click here</a> to log in.)</em>', info_msg, link)
        self.info(info_msg)

    def message(self, message, level=messages.INFO):
        messages.add_message(self.request, level, message)

    def info(self, message):
        return self.message(message, level=messages.INFO)

    def success(self, message):
        return self.message(message, level=messages.SUCCESS)

    def warning(self, message):
        return self.message(message, level=messages.WARNING)

    def error(self, message):
        return self.message(message, level=messages.ERROR)

    def get_context_data(self, **kwargs):
        email = self.request.session.get("logged_in_email")
        return {
            "DEBUG": settings.DEBUG,
            "TITLE": self.title,
            "STATION_NAME": config.STATION_NAME,
            "USER_SUBMIT_ACTIVE": config.USER_SUBMIT_ACTIVE,
            "REJECT_SILENCE_LENGTH": config.REJECT_SILENCE_LENGTH,
            "CURRENT_YEAR": timezone.now().strftime("%Y"),
            "TOMATO_VERSION": settings.TOMATO_VERSION,
            "HAS_FOOTER": bool(config.USER_SUBMIT_CONTENT_BLOCK_FOOTER_COPYRIGHT.strip()),
            "LOGGED_IN_EMAIL": email,
            "IS_LOGGED_IN": bool(email),
            "CSS_COLORS": (
                ("info", "#00bafe", "#0095cb", "#000000"),
                ("success", "#00d390", "#00a06d", "#000000"),
                ("warning", "#fcb700", "#c99200", "#000000"),
                ("error", "#ff637d", "#ff3052", "#630010"),
            ),
            **super().get_context_data(**kwargs),
        }


class LandingView(SubmitMixin, generic.TemplateView):
    def get_context_data(self, **kwargs):
        context = {
            "LOGIN_URL": self.resolve_url("login"),
            "CREATE_URL": self.resolve_url("create"),
            **super().get_context_data(**kwargs),
        }
        if context["IS_LOGGED_IN"]:
            email = context["LOGGED_IN_EMAIL"]
            context.update({
                "SUBMISSIONS": Submission.objects.filter(created_by=email),
            })
        return context


class VerifyView(SubmitMixin, generic.View):
    def get(self, request, *args, **kwargs):
        if getattr(config, "USER_SUBMIT_LOGIN_VIA_EMAIL", False):
            session_token = request.session.get("token")
            if session_token is None:
                self.warning("Invalid link! Please try logging in again.")
            else:
                email, session_token, expires = session_token
                del request.session["token"]
                if secrets.compare_digest(kwargs["token"], session_token):
                    if expires <= timezone.now():
                        self.warning(
                            "The link you provided has expired. A new one has been generated and emailed to you."
                        )
                        self.send_verify_email(email)
                    else:
                        self.success(f"You have been successfully logged in as {email}.")
                        request.session["logged_in_email"] = email
                else:
                    self.warning("Invalid link! Please try logging in again.")

        return HttpResponseRedirect(self.resolve_url("landing"))


class LoginView(SubmitMixin, generic.FormView):
    form_class = LoginForm
    title = "Sign In Page"
    success_url = "landing"

    def get_context_data(self, **kwargs):
        return {
            "CAPTCHA_MAX_LENGTH": SUBMIT_LOGIN_CAPTCHA_MAX_LENGTH,
            **super().get_context_data(**kwargs),
        }

    def form_invalid(self, form):
        self.error("There was a problem and we could not log you in. See below.")
        return super().form_invalid(form)

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if getattr(config, "USER_SUBMIT_LOGIN_VIA_EMAIL", False):  # Might not exist if EMAIL_ENABLED=0
            self.send_verify_email(email)
        else:
            self.success(f"You have been successfully logged in as {email}!")
            self.request.session.update({
                "logged_in_email": form.cleaned_data["email"],
            })
        return super().form_valid(form)


class LogoutView(SubmitMixin, generic.View):
    def dispatch(self, request, *args, **kwargs):
        self.warning("You have been logged out.")
        self.request.session.pop("logged_in_email", None)
        return HttpResponseRedirect(self.resolve_url("landing"))


class CreateView(SubmitMixin, SuccessMessageMixin, generic.CreateView):
    form_class = SubmissionForm
    success_url = "landing"
    success_message = "Submission has been created!"
