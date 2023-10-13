from django import forms
from django.views.generic import FormView

from .base import AdminViewMixin


class AdminDataForm(forms.Form):
    test = forms.TextInput()


class AdminDataView(AdminViewMixin, FormView):
    form_class = AdminDataForm
    name = "data"
    title = "Manage asset data"
