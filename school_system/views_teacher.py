import json
from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView, View,
)
from django.contrib import messages
from django.db import models, transaction
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    TimetableSlot, LiveClassSession, AttendanceRecord,
    StudentProfile, ClassRoom, Grade, Subject,
    Assessment, Question, AnswerOption, AssessmentSubmission,
    DocumentShare, DocumentAccessLog,
)
from .forms import (
    TimetableSlotForm, LiveClassSessionForm,
    AssessmentForm, QuestionForm, AnswerOptionFormSet,
    SubmissionReviewForm, DocumentShareForm,
)
from .mixins import TeacherRequiredMixin
from .utils import AssessmentStatistics, get_file_type
from .notifications import (
    notify_session_confirmed, notify_session_started, notify_session_cancelled,
)


class TimetableView(TeacherRequiredMixin, TemplateView):
    template_name = 'teacher/timetable.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        grade_id = self.request.GET.get('grade_id')

        slots = TimetableSlot.objects.filter(
            teacher=teacher, is_active=True
        ).select_related('subject', 'classroom', 'classroom__grade')

        if grade_id:
            slots = slots.filter(classroom__grade__id=grade_id)

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

        teacher_grades = Grade.objects.filter(
            id__in=slots.values_list('classroom__grade', flat=True).distinct()
        ) if not grade_id else Grade.objects.filter(id=grade_id)

        ctx.update({
            'day_data': day_data,
            'total_hours': total_hours,
            'total_slots': slots.count(),
            'subjects': teacher.subjects.all(),
            'teacher_grades': teacher_grades,
            'selected_grade_id': int(grade_id) if grade_id else None,
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


# ── Assessment Teacher Views ──

class AssessmentListView(TeacherRequiredMixin, ListView):
    model = Assessment
    template_name = 'teacher/assessment_list.html'
    context_object_name = 'assessments'
    paginate_by = 20

    def get_queryset(self):
        qs = Assessment.objects.filter(
            teacher=self.request.user.teacher_profile
        ).select_related('subject', 'classroom', 'grade').order_by('-created_at')

        asst_type = self.request.GET.get('type')
        if asst_type in ('QUIZ', 'HOMEWORK'):
            qs = qs.filter(type=asst_type)

        status = self.request.GET.get('status')
        if status == 'published':
            qs = qs.filter(is_published=True)
        elif status == 'draft':
            qs = qs.filter(is_published=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_qs = Assessment.objects.filter(teacher=self.request.user.teacher_profile)
        stats = AssessmentStatistics()
        ctx.update({
            'total_assessments': all_qs.count(),
            'avg_submission_rate': stats.get_submission_rate(all_qs.first()) if all_qs.exists() else 0,
            'avg_score': stats.get_class_average(all_qs.first()) if all_qs.exists() else 0,
            'current_type': self.request.GET.get('type', ''),
            'current_status': self.request.GET.get('status', ''),
        })
        return ctx


class AssessmentCreateView(TeacherRequiredMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = 'teacher/assessment_form.html'
    success_url = reverse_lazy('teacher_assessments')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        form.instance.teacher = self.request.user.teacher_profile
        messages.success(self.request, 'Assessment created.')
        return super().form_valid(form)


class AssessmentUpdateView(TeacherRequiredMixin, UpdateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = 'teacher/assessment_form.html'
    success_url = reverse_lazy('teacher_assessments')

    def get_queryset(self):
        return Assessment.objects.filter(teacher=self.request.user.teacher_profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Assessment updated.')
        return super().form_valid(form)


class AssessmentDeleteView(TeacherRequiredMixin, DeleteView):
    model = Assessment
    template_name = 'teacher/assessment_confirm_delete.html'
    success_url = reverse_lazy('teacher_assessments')

    def get_queryset(self):
        return Assessment.objects.filter(teacher=self.request.user.teacher_profile)

    def form_valid(self, form):
        messages.success(self.request, 'Assessment deleted.')
        return super().form_valid(form)


class AssessmentPublishView(TeacherRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        assessment = get_object_or_404(
            Assessment, pk=kwargs['pk'],
            teacher=request.user.teacher_profile,
        )
        if assessment.is_published:
            assessment.unpublish()
            messages.success(request, 'Assessment unpublished.')
        else:
            assessment.publish()
            messages.success(request, 'Assessment published.')
        return redirect('teacher_assessments')


class QuestionManagementView(TeacherRequiredMixin, DetailView):
    model = Assessment
    template_name = 'teacher/question_management.html'
    context_object_name = 'assessment'

    def get_queryset(self):
        return Assessment.objects.filter(
            teacher=self.request.user.teacher_profile
        ).prefetch_related('questions__options')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['questions'] = self.object.questions.all()
        return ctx


class QuestionCreateView(TeacherRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'teacher/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment, pk=kwargs['assessment_id'],
            teacher=request.user.teacher_profile,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assessment'] = self.assessment
        if self.request.POST and self.request.POST.get('question_type') == 'MCQ':
            ctx['option_formset'] = AnswerOptionFormSet(self.request.POST)
        else:
            ctx['option_formset'] = AnswerOptionFormSet()
        return ctx

    def form_valid(self, form):
        form.instance.assessment = self.assessment
        response = super().form_valid(form)

        if form.instance.question_type == 'MCQ':
            option_formset = AnswerOptionFormSet(
                self.request.POST, instance=form.instance
            )
            if option_formset.is_valid():
                option_formset.save()
            else:
                return self.form_invalid(form)

        messages.success(self.request, 'Question added.')
        return response

    def get_success_url(self):
        return reverse_lazy('assessment_questions', kwargs={'pk': self.assessment.pk})


class QuestionUpdateView(TeacherRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'teacher/question_form.html'

    def get_queryset(self):
        return Question.objects.filter(assessment__teacher=self.request.user.teacher_profile)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assessment'] = self.object.assessment
        if self.request.POST:
            ctx['option_formset'] = AnswerOptionFormSet(
                self.request.POST, instance=self.object
            )
        else:
            ctx['option_formset'] = AnswerOptionFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.question_type == 'MCQ':
            option_formset = AnswerOptionFormSet(
                self.request.POST, instance=form.instance
            )
            if option_formset.is_valid():
                option_formset.save()
        messages.success(self.request, 'Question updated.')
        return response

    def get_success_url(self):
        return reverse_lazy(
            'assessment_questions', kwargs={'pk': self.object.assessment.pk}
        )


class QuestionDeleteView(TeacherRequiredMixin, DeleteView):
    model = Question
    template_name = 'teacher/question_confirm_delete.html'

    def get_queryset(self):
        return Question.objects.filter(assessment__teacher=self.request.user.teacher_profile)

    def get_success_url(self):
        return reverse_lazy(
            'assessment_questions', kwargs={'pk': self.object.assessment.pk}
        )

    def form_valid(self, form):
        messages.success(self.request, 'Question deleted.')
        return super().form_valid(form)


class AssessmentSubmissionsView(TeacherRequiredMixin, TemplateView):
    template_name = 'teacher/submissions_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        assessment = get_object_or_404(
            Assessment.objects.select_related('subject', 'classroom', 'grade'),
            pk=self.kwargs['pk'],
            teacher=self.request.user.teacher_profile,
        )
        submissions = assessment.submissions.select_related(
            'student__user'
        ).order_by('-submitted_at')

        stats = AssessmentStatistics()
        scores = [s.score for s in submissions if s.score is not None]

        ctx.update({
            'assessment': assessment,
            'submissions': submissions,
            'total_students': assessment.get_target_students().count(),
            'submitted_count': submissions.count(),
            'avg_score': stats.get_class_average(assessment),
            'highest_score': max(scores) if scores else 0,
            'lowest_score': min(scores) if scores else 0,
        })
        return ctx


class SubmissionDetailView(TeacherRequiredMixin, DetailView):
    model = AssessmentSubmission
    template_name = 'teacher/submission_detail.html'
    context_object_name = 'submission'

    def get_queryset(self):
        return AssessmentSubmission.objects.filter(
            assignment__teacher=self.request.user.teacher_profile
        ).select_related(
            'student__user', 'assignment__subject'
        ).prefetch_related(
            'student_answers__question__options',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        submission = self.object
        questions = submission.assignment.questions.prefetch_related('options').order_by('order')
        answers = {a.question_id: a for a in submission.student_answers.all()}

        question_data = []
        for q in questions:
            ans = answers.get(q.pk)
            question_data.append({
                'question': q,
                'answer': ans,
                'student_value': submission.submitted_answers.get(str(q.pk)),
            })

        ctx.update({
            'questions_data': question_data,
            'form': SubmissionReviewForm(initial={
                'final_score': submission.score or 0,
                'feedback': submission.feedback,
                'is_verified': submission.is_verified_by_teacher,
            }),
        })
        return ctx


class SubmissionGradeView(TeacherRequiredMixin, UpdateView):
    model = AssessmentSubmission
    form_class = SubmissionReviewForm
    template_name = 'teacher/submission_grade.html'
    success_url = reverse_lazy('teacher_assessments')

    def get_queryset(self):
        return AssessmentSubmission.objects.filter(
            assignment__teacher=self.request.user.teacher_profile
        )

    def form_valid(self, form):
        submission = self.object
        submission.mark_as_graded(
            score=form.cleaned_data['final_score'],
            feedback=form.cleaned_data.get('feedback', ''),
            teacher_override=form.cleaned_data.get('is_verified', False),
        )
        messages.success(self.request, 'Submission graded.')
        return redirect(
            'teacher_submissions', pk=submission.assignment.pk
        )


class BulkGradeView(TeacherRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

        updated = 0
        with transaction.atomic():
            for sub_id, grade_data in data.items():
                try:
                    submission = AssessmentSubmission.objects.get(
                        pk=sub_id,
                        assignment__teacher=request.user.teacher_profile,
                    )
                except AssessmentSubmission.DoesNotExist:
                    continue
                submission.mark_as_graded(
                    score=grade_data.get('score', 0),
                    feedback=grade_data.get('feedback', ''),
                    teacher_override=grade_data.get('verify', False),
                )
                updated += 1

        return JsonResponse({'success': True, 'updated': updated})


def get_school_subjects(request):
    school_id = request.GET.get('school_id')
    if not school_id:
        return JsonResponse([], safe=False)
    subjects = Subject.objects.filter(schools__id=school_id).values('id', 'name', 'code')
    return JsonResponse(list(subjects), safe=False)


def get_grade_classrooms(request):
    grade_id = request.GET.get('grade_id')
    if not grade_id:
        return JsonResponse([], safe=False)
    rooms = ClassRoom.objects.filter(grade__id=grade_id, is_active=True).values('id', 'name')
    return JsonResponse(list(rooms), safe=False)


def get_classroom_students(request):
    classroom_id = request.GET.get('classroom_id')
    if not classroom_id:
        return JsonResponse([], safe=False)
    students = StudentProfile.objects.filter(
        classroom__id=classroom_id
    ).select_related('user')
    students_list = [
        {
            'id': s.id,
            'student_id': s.student_id,
            'full_name': s.full_name,
        }
        for s in students
    ]
    return JsonResponse(students_list, safe=False)


# ─────────────────────── DOCUMENT SHARING (Teacher) ───────────────────────

class DocumentListView(TeacherRequiredMixin, ListView):
    model = DocumentShare
    template_name = 'teacher/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = DocumentShare.objects.filter(
            owner_teacher=self.request.user.teacher_profile
        ).select_related('category', 'subject').prefetch_related('allowed_classes')
        file_type = self.request.GET.get('file_type')
        if file_type:
            qs = qs.filter(file_type=file_type)
        subject_id = self.request.GET.get('subject')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        visibility = self.request.GET.get('visibility')
        if visibility == 'public':
            qs = qs.filter(is_public=True)
        elif visibility == 'private':
            qs = qs.filter(is_public=False)
        return qs.order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        docs = DocumentShare.objects.filter(owner_teacher=teacher)
        total_downloads = sum(d.download_count for d in docs)
        total_views = sum(d.view_count for d in docs)
        total_storage = sum(d.file_size for d in docs)
        ctx.update({
            'total_documents': docs.count(),
            'total_downloads': total_downloads,
            'total_views': total_views,
            'total_storage_mb': round(total_storage / (1024 * 1024), 2),
            'file_types': DocumentShare.FILE_TYPE_CHOICES,
            'subjects': teacher.subjects.all(),
            'current_file_type': self.request.GET.get('file_type', ''),
            'current_subject': self.request.GET.get('subject', ''),
            'current_visibility': self.request.GET.get('visibility', ''),
        })
        return ctx


class DocumentCreateView(TeacherRequiredMixin, CreateView):
    model = DocumentShare
    form_class = DocumentShareForm
    template_name = 'teacher/document_form.html'

    def get_success_url(self):
        return reverse_lazy('document_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        form.instance.owner_teacher = self.request.user.teacher_profile
        uploaded = self.request.FILES.get('file_upload')
        if uploaded:
            form.instance.file_size = uploaded.size
            form.instance.mime_type = uploaded.content_type or ''
            form.instance.file_type = get_file_type(
                uploaded.content_type or '', uploaded.name
            )
        return super().form_valid(form)


class DocumentUpdateView(TeacherRequiredMixin, UpdateView):
    model = DocumentShare
    form_class = DocumentShareForm
    template_name = 'teacher/document_form.html'
    success_url = reverse_lazy('teacher_documents')

    def get_queryset(self):
        return DocumentShare.objects.filter(
            owner_teacher=self.request.user.teacher_profile
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs


class DocumentDeleteView(TeacherRequiredMixin, DeleteView):
    model = DocumentShare
    template_name = 'teacher/document_confirm_delete.html'
    success_url = reverse_lazy('teacher_documents')

    def get_queryset(self):
        return DocumentShare.objects.filter(
            owner_teacher=self.request.user.teacher_profile
        )


class DocumentDetailView(TeacherRequiredMixin, DetailView):
    model = DocumentShare
    template_name = 'teacher/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        return DocumentShare.objects.filter(
            owner_teacher=self.request.user.teacher_profile
        ).select_related('category', 'subject').prefetch_related(
            'allowed_classes', 'allowed_students__user'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doc = self.object
        logs = DocumentAccessLog.objects.filter(document=doc).select_related(
            'student__user'
        ).order_by('-accessed_at')[:50]
        unique_students = DocumentAccessLog.objects.filter(
            document=doc
        ).values('student').distinct().count()
        ctx.update({
            'access_logs': logs,
            'unique_students': unique_students,
        })
        return ctx


class DocumentAnalyticsView(TeacherRequiredMixin, TemplateView):
    template_name = 'teacher/document_analytics.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        docs = DocumentShare.objects.filter(owner_teacher=teacher)

        total_downloads = sum(d.download_count for d in docs)
        total_views = sum(d.view_count for d in docs)
        total_storage = sum(d.file_size for d in docs)

        most_downloaded = docs.order_by('-download_count').first()
        most_viewed = docs.order_by('-view_count').first()

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        daily_logs_data = DocumentAccessLog.objects.filter(
            document__owner_teacher=teacher,
            accessed_at__gte=thirty_days_ago,
        ).annotate(
            date=TruncDate('accessed_at')
        ).values('date').annotate(
            total=models.Count('id')
        ).order_by('date')

        import json
        from datetime import date as date_type
        class DateEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (date_type, timezone.datetime)):
                    return obj.isoformat()
                return super().default(obj)

        daily_logs_json = json.dumps(
            [{'date': str(d['date']), 'total': d['total']} for d in daily_logs_data],
            cls=DateEncoder,
        )

        file_type_dist = {}
        for doc in docs:
            ft = doc.file_type
            file_type_dist[ft] = file_type_dist.get(ft, 0) + 1
        file_type_dist_json = json.dumps(file_type_dist, cls=DateEncoder)

        recent_logs = DocumentAccessLog.objects.filter(
            document__owner_teacher=teacher,
        ).select_related(
            'document', 'student__user'
        ).order_by('-accessed_at')[:20]

        ctx.update({
            'documents': docs,
            'total_documents': docs.count(),
            'total_downloads': total_downloads,
            'total_views': total_views,
            'total_storage_mb': round(total_storage / (1024 * 1024), 2),
            'most_downloaded': most_downloaded,
            'most_viewed': most_viewed,
            'daily_logs_json': daily_logs_json,
            'file_type_dist_json': file_type_dist_json,
            'recent_logs': recent_logs,
        })
        return ctx
