from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

from .models import TeacherProfile, StudentProfile
from .forms import (
    CustomAuthenticationForm, TeacherRegistrationForm,
    StudentRegistrationForm,
)

User = get_user_model()


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.role == 'teacher':
            return reverse_lazy('teacher_dashboard')
        elif user.role == 'student':
            return reverse_lazy('student_dashboard')
        return reverse_lazy('login')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


class TeacherRegisterView(CreateView):
    model = User
    form_class = TeacherRegistrationForm
    template_name = 'registration/teacher_register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.role = 'teacher'
        user.save()

        TeacherProfile.objects.create(
            user=user,
            employee_id=form.cleaned_data['employee_id'],
            school=form.cleaned_data['school'],
            qualifications=form.cleaned_data['qualifications'],
            experience_years=form.cleaned_data['experience_years'],
            specialization=form.cleaned_data.get('specialization', ''),
            office_room=form.cleaned_data.get('office_room', ''),
            hire_date=form.cleaned_data['hire_date'],
        )

        teacher_profile = TeacherProfile.objects.get(user=user)
        teacher_profile.subjects.set(form.cleaned_data['subjects'])

        messages.success(self.request, 'Registration successful! Please log in.')
        return response


class StudentRegisterView(CreateView):
    model = User
    form_class = StudentRegistrationForm
    template_name = 'registration/student_register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.role = 'student'
        user.save()

        classroom = form.cleaned_data['classroom']
        grade = form.cleaned_data['grade']

        StudentProfile.objects.create(
            user=user,
            student_id=form.cleaned_data['student_id'],
            school=form.cleaned_data['school'],
            classroom=classroom,
            grade=grade,
            date_of_birth=form.cleaned_data['date_of_birth'],
            gender=form.cleaned_data['gender'],
            address=form.cleaned_data.get('address', ''),
            parent_name=form.cleaned_data['parent_name'],
            parent_phone=form.cleaned_data['parent_phone'],
            parent_email=form.cleaned_data.get('parent_email', ''),
            emergency_contact_name=form.cleaned_data['emergency_contact_name'],
            emergency_contact_phone=form.cleaned_data['emergency_contact_phone'],
        )

        classroom.current_enrollment += 1
        classroom.save()

        messages.success(self.request, 'Registration successful! Please log in.')
        return response
