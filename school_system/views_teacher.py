import json
from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, View,
)
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    TimetableSlot, LiveClassSession, AttendanceRecord,
    StudentProfile, ClassRoom, School, Grade, Subject,
)
from .forms import TimetableSlotForm, LiveClassSessionForm
from .mixins import TeacherRequiredMixin
from .notifications import (
    notify_session_confirmed, notify_session_started, notify_session_cancelled,
)


class TimetableView(TeacherRequiredMixin, TemplateView):
    template_name = 'teacher/timetable.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        slots = TimetableSlot.objects.filter(
            teacher=teacher, is_active=True
        ).select_related('subject', 'classroom', 'classroom__grade')

        slots_by_day = {}
        for i in range(7):
            slots_by_day[i] = slots.filter(day_of_week=i)

        total_mins = sum(s.duration_mins for s in slots)
        total_hours = round(total_mins / 60, 1) if total_mins else 0

        day_choices = dict(TimetableSlot.DAY_CHOICES)
        day_data = []
        for i in range(7):
            day_data.append({
                'num': i,
                'name': day_choices.get(i, ''),
                'slots': slots_by_day[i],
            })

        ctx.update({
            'day_data': day_data,
            'total_hours': total_hours,
            'total_slots': slots.count(),
            'subjects': teacher.subjects.all(),
            'classrooms': ClassRoom.objects.filter(
                grade__school=teacher.school, is_active=True
            ).select_related('grade'),
        })
        return ctx


class TimetableSlotCreateView(TeacherRequiredMixin, CreateView):
    model = TimetableSlot
    form_class = TimetableSlotForm
    template_name = 'teacher/timetable_form.html'
    success_url = reverse_lazy('teacher_timetable')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        form.instance.teacher = self.request.user.teacher_profile
        messages.success(self.request, 'Timetable slot created.')
        return super().form_valid(form)


class TimetableSlotUpdateView(TeacherRequiredMixin, UpdateView):
    model = TimetableSlot
    form_class = TimetableSlotForm
    template_name = 'teacher/timetable_form.html'
    success_url = reverse_lazy('teacher_timetable')

    def get_queryset(self):
        return TimetableSlot.objects.filter(teacher=self.request.user.teacher_profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Timetable slot updated.')
        return super().form_valid(form)


class TimetableSlotDeleteView(TeacherRequiredMixin, DeleteView):
    model = TimetableSlot
    template_name = 'teacher/timetable_confirm_delete.html'
    success_url = reverse_lazy('teacher_timetable')

    def get_queryset(self):
        return TimetableSlot.objects.filter(teacher=self.request.user.teacher_profile)

    def form_valid(self, form):
        messages.success(self.request, 'Timetable slot deleted.')
        return super().form_valid(form)


class LiveClassSessionListView(TeacherRequiredMixin, ListView):
    model = LiveClassSession
    template_name = 'teacher/live_sessions_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        qs = LiveClassSession.objects.filter(
            timetable_slot__teacher=self.request.user.teacher_profile
        ).select_related(
            'timetable_slot__subject', 'timetable_slot__classroom',
            'timetable_slot__teacher',
        ).order_by('-session_date', '-created_at')

        status_filter = self.request.GET.get('status')
        if status_filter in ('DRAFT', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'):
            qs = qs.filter(status=status_filter)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_sessions = LiveClassSession.objects.filter(
            timetable_slot__teacher=self.request.user.teacher_profile
        )
        total = all_sessions.count()
        completed = all_sessions.filter(status='COMPLETED').count()
        ctx.update({
            'total_sessions': total,
            'completion_rate': round((completed / total) * 100, 1) if total else 0,
            'current_filter': self.request.GET.get('status', ''),
        })
        return ctx


class LiveClassSessionCreateView(TeacherRequiredMixin, CreateView):
    model = LiveClassSession
    form_class = LiveClassSessionForm
    template_name = 'teacher/live_session_form.html'
    success_url = reverse_lazy('teacher_live_sessions')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slot_id = self.kwargs.get('timetable_slot_id')
        slot = get_object_or_404(
            TimetableSlot,
            pk=slot_id,
            teacher=self.request.user.teacher_profile,
        )
        ctx['timetable_slot'] = slot
        return ctx

    def form_valid(self, form):
        slot_id = self.kwargs.get('timetable_slot_id')
        slot = get_object_or_404(
            TimetableSlot,
            pk=slot_id,
            teacher=self.request.user.teacher_profile,
        )
        form.instance.timetable_slot = slot
        form.instance.status = 'DRAFT'
        messages.success(self.request, 'Live class session created.')
        return super().form_valid(form)


class LiveClassControlView(TeacherRequiredMixin, UpdateView):
    model = LiveClassSession
    fields = []
    template_name = 'teacher/live_session_control.html'
    success_url = reverse_lazy('teacher_live_sessions')

    def get_queryset(self):
        return LiveClassSession.objects.filter(
            timetable_slot__teacher=self.request.user.teacher_profile
        ).select_related(
            'timetable_slot__subject', 'timetable_slot__classroom',
            'timetable_slot__teacher',
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        action = request.POST.get('action')

        if action == 'confirm':
            obj.confirm()
            notify_session_confirmed(obj)
            messages.success(request, 'Class confirmed.')
        elif action == 'start':
            obj.start()
            notify_session_started(obj)
            messages.success(request, 'Class started.')
        elif action == 'complete':
            obj.complete()
            messages.success(request, 'Class completed.')
        elif action == 'cancel':
            obj.cancel()
            notify_session_cancelled(obj)
            messages.success(request, 'Class cancelled.')
        else:
            messages.error(request, 'Unknown action.')

        return redirect('teacher_live_sessions')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session = self.object
        students = StudentProfile.objects.filter(classroom=session.classroom)
        records = {
            r.student_id: r
            for r in session.attendance_logs.select_related('student__user').all()
        }
        ctx.update({
            'students': students,
            'attendance_records': records,
            'present_count': session.get_present_count(),
            'student_count': session.get_student_count(),
            'attendance_pct': session.get_attendance_percentage(),
        })
        return ctx


class AttendanceManagementView(TeacherRequiredMixin, TemplateView):
    template_name = 'teacher/attendance_management.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(
            LiveClassSession.objects.select_related(
                'timetable_slot__subject', 'timetable_slot__classroom',
            ),
            pk=session_id,
            timetable_slot__teacher=self.request.user.teacher_profile,
        )
        students = StudentProfile.objects.filter(
            classroom=session.classroom
        ).select_related('user').order_by('user__first_name', 'user__last_name')

        existing = {
            r.student_id: r
            for r in session.attendance_logs.select_related('student__user').all()
        }

        attendance_grid = []
        for s in students:
            record = existing.get(s.id)
            attendance_grid.append({
                'student': s,
                'record': record,
                'status': record.status if record else None,
                'check_in': record.check_in_time if record else None,
            })

        ctx.update({
            'session': session,
            'students': students,
            'attendance_grid': attendance_grid,
            'existing_records': existing,
            'present_count': session.get_present_count(),
            'student_count': session.get_student_count(),
        })
        return ctx


class BulkAttendanceSaveView(TeacherRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        session = get_object_or_404(
            LiveClassSession,
            pk=session_id,
            timetable_slot__teacher=request.user.teacher_profile,
        )

        try:
            data = json.loads(request.POST.get('attendance_data', '{}'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

        with transaction.atomic():
            for student_id, status in data.items():
                try:
                    student = StudentProfile.objects.get(pk=student_id)
                except StudentProfile.DoesNotExist:
                    continue

                defaults = {'status': status, 'updated_at': timezone.now()}
                if status == 'PRESENT' and not AttendanceRecord.objects.filter(
                    session=session, student=student
                ).exists():
                    defaults['check_in_time'] = timezone.now()

                AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults=defaults,
                )

        session.attendance_taken = True
        session.save(update_fields=['attendance_taken', 'updated_at'])

        return JsonResponse({'success': True, 'message': 'Attendance saved successfully.'})


def get_school_subjects(request):
    school_id = request.GET.get('school_id')
    if not school_id:
        return JsonResponse([], safe=False)
    subjects = Subject.objects.filter(schools__id=school_id).values('id', 'name', 'code')
    return JsonResponse(list(subjects), safe=False)


class ClassRoomCreateView(TeacherRequiredMixin, CreateView):
    model = ClassRoom
    template_name = 'teacher/classroom_form.html'
    fields = ['grade', 'name', 'room_number', 'capacity']
    success_url = reverse_lazy('teacher_timetable')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        teacher = self.request.user.teacher_profile
        form.fields['grade'].queryset = Grade.objects.filter(
            school=teacher.school, is_active=True
        )
        form.fields['grade'].widget.attrs['class'] = 'form-control'
        form.fields['name'].widget.attrs['class'] = 'form-control'
        form.fields['name'].widget.attrs['dir'] = 'rtl'
        form.fields['room_number'].widget.attrs['class'] = 'form-control'
        form.fields['capacity'].widget.attrs['class'] = 'form-control'
        form.fields['capacity'].initial = 30
        return form

    def form_valid(self, form):
        teacher = self.request.user.teacher_profile
        form.instance.grade = form.cleaned_data['grade']
        messages.success(self.request, f'Class {form.instance.name} created.')
        return super().form_valid(form)
