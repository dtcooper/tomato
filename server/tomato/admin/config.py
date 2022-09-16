from constance.admin import Config
from constance.admin import ConstanceAdmin as ConstanceConfigAdmin
from constance.apps import ConstanceConfig


Config._meta.verbose_name = Config._meta.verbose_name_plural = "configuration"
ConstanceConfig.verbose_name = "Settings"


class ConfigAdmin(ConstanceConfigAdmin):
    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True
