from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages


class RoleRequiredMixin(LoginRequiredMixin):
    required_role = None
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != self.required_role:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(self.get_login_url())
        return super().dispatch(request, *args, **kwargs)

    def get_login_url(self):
        return self.login_url


class AdminRequiredMixin(RoleRequiredMixin):
    required_role = 'ADMIN'


class SuperAdminRequiredMixin(RoleRequiredMixin):
    required_role = 'SUPERADMIN'
