from constance.admin import Config
from constance.admin import ConstanceAdmin as ConstanceConfigAdmin
from constance.apps import ConstanceConfig
from constance.forms import ConstanceForm

from ..utils import mark_models_dirty


Config._meta.verbose_name = Config._meta.verbose_name_plural = "configuration"
ConstanceConfig.verbose_name = "Settings"


class ConfigForm(ConstanceForm):
    def __init__(self, initial, request=None, *args, **kwargs):
        self.request = request
        super().__init__(initial, request, *args, **kwargs)

    def save(self):
        super().save()
        mark_models_dirty(self.request)


class ConfigAdmin(ConstanceConfigAdmin):
    change_list_form = ConfigForm

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True
