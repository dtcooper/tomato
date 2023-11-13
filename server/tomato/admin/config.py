from constance.admin import Config, ConstanceAdmin as ConstanceConfigAdmin
from constance.apps import ConstanceConfig
from constance.forms import ConstanceForm

from ..utils import send_config_update_redis_message


Config._meta.verbose_name = Config._meta.verbose_name_plural = "configuration"
ConstanceConfig.verbose_name = "Settings"


class ConfigForm(ConstanceForm):
    def save(self):
        super().save()
        send_config_update_redis_message()


class ConfigAdmin(ConstanceConfigAdmin):
    change_list_form = ConfigForm

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True
