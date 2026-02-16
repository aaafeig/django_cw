class ManagerAccessMixin:

    def is_manager(self):
        return self.request.user.groups.filter(name="Manager").exists()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.is_manager():
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_manager"] = self.is_manager()
        return context