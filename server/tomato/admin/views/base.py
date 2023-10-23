from django.core.exceptions import PermissionDenied


class AdminViewMixin:
    title = "Untitled"
    path = None
    perms = None
    template_name = None

    def __init__(self, admin_site, *args, **kwargs):
        self.admin_site = admin_site
        super().__init__(*args, **kwargs)

    @classmethod
    def as_view(cls, admin_site, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        view.view_initkwargs["admin_site"] = admin_site
        return view

    @classmethod
    def check_perms(cls, request):
        return cls.perms is None or request.user.has_perms(cls.perms)

    def dispatch(self, request, *args, **kwargs):
        if not self.check_perms(request):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [f"admin/extra/{self.name}.html" if self.template_name is None else f"admin/extra/{self.template_name}"]

    @classmethod
    def get_path(cls):
        return f"{cls.name}/" if cls.path is None else cls.path

    def get_context_data(self, **kwargs):
        return {
            **self.admin_site.each_context(self.request),
            "title": self.title,
            **super().get_context_data(**kwargs),
        }
