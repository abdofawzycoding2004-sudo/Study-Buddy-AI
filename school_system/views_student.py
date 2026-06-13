from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib import messages
from django.utils import timezone

from .models import Assessment, AssessmentSubmission
from .forms import StudentAnswerForm
from .mixins import StudentRequiredMixin


class StudentAssessmentListView(StudentRequiredMixin, ListView):
    model = Assessment
    template_name = 'student/assessment_list.html'
    context_object_name = 'assessments'

    def get_queryset(self):
        student = self.request.user.student_profile
        return Assessment.objects.filter(
            is_published=True,
            grade=student.grade,
        ).filter(
            classroom=student.classroom
        ).select_related(
            'subject', 'classroom', 'teacher__user'
        ).order_by('due_date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.request.user.student_profile
        now = timezone.now()

        upcoming, available, completed, overdue = [], [], [], []
        for a in ctx['assessments']:
            submitted = AssessmentSubmission.objects.filter(
                assignment=a, student=student
            ).first()
            if submitted:
                completed.append(a)
            elif a.is_overdue:
                overdue.append(a)
            elif a.available_from <= now:
                available.append(a)
            else:
                upcoming.append(a)

        ctx.update({
            'upcoming': upcoming,
            'available': available,
            'completed': completed,
            'overdue': overdue,
        })
        return ctx


class StudentAssessmentDetailView(StudentRequiredMixin, DetailView):
    model = Assessment
    template_name = 'student/assessment_detail.html'
    context_object_name = 'assessment'

    def get_queryset(self):
        student = self.request.user.student_profile
        return Assessment.objects.filter(
            is_published=True,
            grade=student.grade,
            classroom=student.classroom,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.request.user.student_profile
        assessment = self.object
        now = timezone.now()

        submission = AssessmentSubmission.objects.filter(
            assignment=assessment, student=student
        ).first()

        can_submit = (
            assessment.is_active
            and not assessment.is_overdue
            and not submission
        )

        time_remaining = None
        if assessment.time_limit_mins and can_submit:
            time_remaining = assessment.time_limit_mins * 60

        ctx.update({
            'submission': submission,
            'can_submit': can_submit,
            'time_remaining': time_remaining,
            'is_overdue': assessment.is_overdue,
            'now': now,
        })
        return ctx


class StudentAssessmentSubmitView(StudentRequiredMixin, CreateView):
    model = AssessmentSubmission
    template_name = 'student/assessment_submit.html'

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment, pk=kwargs['pk'],
            is_published=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        questions = self.assessment.questions.prefetch_related('options').order_by('order')
        ctx['assessment'] = self.assessment
        ctx['questions'] = questions
        if self.request.POST:
            ctx['form'] = StudentAnswerForm(
                self.request.POST, questions=questions
            )
        else:
            ctx['form'] = StudentAnswerForm(questions=questions)
        return ctx

    def form_valid(self, form):
        student = self.request.user.student_profile
        existing = AssessmentSubmission.objects.filter(
            assignment=self.assessment, student=student
        ).exists()
        if existing:
            messages.error(self.request, 'You have already submitted this assessment.')
            return redirect('student_assessment_detail', pk=self.assessment.pk)

        answers = {}
        for field_name, value in form.cleaned_data.items():
            if field_name.startswith('question_'):
                qid = field_name.replace('question_', '')
                answers[qid] = value

        submission = AssessmentSubmission.objects.create(
            assignment=self.assessment,
            student=student,
            submitted_answers=answers,
            is_late=self.assessment.is_overdue,
        )

        if self.assessment.is_overdue:
            penalty = self.assessment.calculate_late_penalty(submission)
            submission.penalty_applied = penalty
            submission.save(update_fields=['penalty_applied'])

        submission.auto_grade()

        messages.success(self.request, 'Assessment submitted successfully!')
        return redirect('student_submission_result', pk=submission.pk)

    def post(self, request, *args, **kwargs):
        questions = self.assessment.questions.prefetch_related('options').order_by('order')
        form = StudentAnswerForm(request.POST, questions=questions)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class StudentSubmissionResultView(StudentRequiredMixin, DetailView):
    model = AssessmentSubmission
    template_name = 'student/submission_result.html'
    context_object_name = 'submission'

    def get_queryset(self):
        return AssessmentSubmission.objects.filter(
            student__user=self.request.user
        ).select_related(
            'assignment__subject', 'assignment__classroom',
        ).prefetch_related(
            'student_answers__question__options',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        submission = self.object
        assessment = submission.assignment
        questions = assessment.questions.prefetch_related('options').order_by('order')

        question_data = []
        for q in questions:
            ans = submission.student_answers.filter(question=q).first()
            student_val = submission.submitted_answers.get(str(q.pk))
            correct_val = None
            if q.question_type == 'MCQ':
                correct = q.options.filter(is_correct=True).first()
                correct_val = str(correct.pk) if correct else None
            elif q.question_type == 'TRUE_FALSE':
                correct = q.options.filter(is_correct=True).first()
                correct_val = correct.option_text if correct else None

            is_correct = None
            if q.is_auto_gradable:
                if q.question_type == 'MCQ':
                    is_correct = student_val == correct_val
                elif q.question_type == 'TRUE_FALSE':
                    is_correct = student_val == correct_val

            question_data.append({
                'question': q,
                'student_answer': ans,
                'student_value': student_val,
                'correct_value': correct_val,
                'is_correct': is_correct,
                'points': q.points,
                'points_earned': ans.points_earned if ans else 0,
            })

        ctx.update({
            'questions_data': question_data,
            'show_answers': assessment.show_correct_answers,
            'max_points': assessment.max_points,
        })
        return ctx
