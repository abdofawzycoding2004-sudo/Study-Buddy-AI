from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages


class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return getattr(self.request.user, 'role', None) == 'teacher'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        raise Http404("You do not have permission to access this page.")
