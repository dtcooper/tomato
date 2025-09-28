from constance.admin import Config, ConstanceAdmin as ConstanceConfigAdmin
from constance.apps import ConstanceConfig


Config._meta.verbose_name = Config._meta.verbose_name_plural = "configuration"
ConstanceConfig.verbose_name = "Settings"


class ConfigAdmin(ConstanceConfigAdmin):
    # TODO: intercept these for api notification

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True
