from constance.admin import Config as Constance
from constance.admin import ConstanceAdmin as BaseConstanceAdmin


class ConstanceAdmin(BaseConstanceAdmin):
    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True


Constance._meta.verbose_name = Constance._meta.verbose_name_plural = "configuration"
