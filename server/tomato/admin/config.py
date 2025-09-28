import logging

from constance.admin import Config, ConstanceAdmin as ConstanceConfigAdmin
from constance.apps import ConstanceConfig
from constance.forms import ConstanceForm as OriginalConstanceForm

from ..utils import notify_api


Config._meta.verbose_name = Config._meta.verbose_name_plural = "configuration"
ConstanceConfig.verbose_name = "Settings"


logger = logging.getLogger(__name__)


class ConstanceForm(OriginalConstanceForm):
    def save(self):
        logger.debug("Constance config was saved in admin UI, notifying API")
        notify_api()
        super().save()


class ConfigAdmin(ConstanceConfigAdmin):
    change_list_form = ConstanceForm

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True
