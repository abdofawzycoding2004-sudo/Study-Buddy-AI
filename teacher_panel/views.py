from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView, UpdateView, ListView, TemplateView, DetailView, View,
)
from django.db import transaction
from django.db.models import Avg, Count, Q, F, Sum, Value, FloatField, DecimalField
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from .mixins import TeacherRequiredMixin
from .models import (
    Course, Module, Material, Assignment, Quiz,
    Question, Choice, AssignmentSubmission, AttendanceSession,
    AttendanceRecord,
)
from .forms import (
    CourseForm, ModuleForm, MaterialForm, AssignmentForm,
    QuizForm, QuestionForm, ChoiceForm, AssignmentGradingForm,
    BulkAttendanceForm, ModuleFormSet, MaterialFormSet, ChoiceFormSet,
)

User = get_user_model()


class CourseContentBuilderView(LoginRequiredMixin, TeacherRequiredMixin, TemplateView):
    template_name = 'teacher_panel/course_builder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'course_form' not in context:
            context['course_form'] = CourseForm(prefix='course')
        if 'module_formset' not in context:
            context['module_formset'] = ModuleFormSet(
                prefix='modules',
                queryset=Module.objects.none(),
            )
        return context

    def post(self, request, *args, **kwargs):
        course_form = CourseForm(request.POST, prefix='course')
        module_formset = ModuleFormSet(
            request.POST, prefix='modules',
            queryset=Module.objects.none(),
        )

        if course_form.is_valid() and module_formset.is_valid():
            with transaction.atomic():
                course = course_form.save(commit=False)
                course.created_by = request.user
                course.save()
                instances = module_formset.save(commit=False)
                for instance in instances:
                    instance.course = course
                    instance.save()
                for obj in module_formset.deleted_objects:
                    obj.delete()
            messages.success(request, 'Course and modules created successfully.')
            return redirect('teacher_panel:course_detail', pk=course.pk)

        context = {
            'course_form': course_form,
            'module_formset': module_formset,
        }
        return self.render_to_response(context)


class CourseListView(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    model = Course
    template_name = 'teacher_panel/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(
            created_by=self.request.user
        ).prefetch_related('modules').order_by('-created_at')


class CourseDetailView(LoginRequiredMixin, TeacherRequiredMixin, DetailView):
    model = Course
    template_name = 'teacher_panel/course_detail.html'
    context_object_name = 'course'

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user).prefetch_related(
            'modules__materials',
            'modules__assignments',
            'modules__quizzes',
        )


class ModuleCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'teacher_panel/module_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(
            Course, pk=kwargs['course_pk'], created_by=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'teacher_panel:course_detail', kwargs={'pk': self.course.pk}
        )


class QuizBuilderView(LoginRequiredMixin, TeacherRequiredMixin, TemplateView):
    template_name = 'teacher_panel/quiz_builder.html'

    def dispatch(self, request, *args, **kwargs):
        self.module = get_object_or_404(
            Module, pk=kwargs['module_pk'],
            course__created_by=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'quiz_form' not in context:
            context['quiz_form'] = QuizForm(prefix='quiz')
        if 'question_formset' not in context:
            context['question_formset'] = ChoiceFormSet(
                prefix='choices',
                queryset=Choice.objects.none(),
            )
        context['module'] = self.module
        return context

    def post(self, request, *args, **kwargs):
        quiz_form = QuizForm(request.POST, prefix='quiz')
        choice_formset = ChoiceFormSet(
            request.POST, prefix='choices',
            queryset=Choice.objects.none(),
        )

        if quiz_form.is_valid() and choice_formset.is_valid():
            with transaction.atomic():
                quiz = quiz_form.save(commit=False)
                quiz.module = self.module
                quiz.save()

                question = Question.objects.create(
                    quiz=quiz,
                    text='',
                    question_type='mcq',
                    points=1,
                )

                instances = choice_formset.save(commit=False)
                for instance in instances:
                    instance.question = question
                    instance.save()
                for obj in choice_formset.deleted_objects:
                    obj.delete()
            messages.success(request, 'Quiz created successfully.')
            return redirect(
                'teacher_panel:course_detail', pk=self.module.course.pk
            )

        context = {
            'quiz_form': quiz_form,
            'question_formset': choice_formset,
            'module': self.module,
        }
        return self.render_to_response(context)


class GradingCenterListView(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    model = AssignmentSubmission
    template_name = 'teacher_panel/grading_list.html'
    context_object_name = 'submissions'

    def get_queryset(self):
        return AssignmentSubmission.objects.select_related(
            'assignment', 'student'
        ).filter(
            assignment__module__course__created_by=self.request.user
        ).order_by('-submitted_at')


class GradingCenterUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = AssignmentSubmission
    form_class = AssignmentGradingForm
    template_name = 'teacher_panel/grading_form.html'
    context_object_name = 'submission'

    def get_queryset(self):
        return AssignmentSubmission.objects.select_related(
            'assignment', 'student'
        ).filter(
            assignment__module__course__created_by=self.request.user
        )

    def get_success_url(self):
        return reverse_lazy('teacher_panel:grading_list')

    def form_valid(self, form):
        messages.success(self.request, 'Grade saved successfully.')
        return super().form_valid(form)


class AttendanceSheetView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher_panel/attendance_sheet.html'

    def get_course(self, course_pk):
        return get_object_or_404(
            Course, pk=course_pk, created_by=self.request.user
        )

    def get_students(self, course):
        return User.objects.filter(
            role='student'
        ).order_by('username')

    def get(self, request, course_pk):
        course = self.get_course(course_pk)
        students = self.get_students(course)
        form = BulkAttendanceForm(students=students)
        sessions = AttendanceSession.objects.filter(course=course).prefetch_related(
            'records__student'
        ).order_by('-session_date')[:10]

        return render(request, self.template_name, {
            'course': course,
            'form': form,
            'sessions': sessions,
            'students': students,
        })

    def post(self, request, course_pk):
        course = self.get_course(course_pk)
        students = self.get_students(course)
        form = BulkAttendanceForm(request.POST, students=students)

        if form.is_valid():
            session_date = form.cleaned_data['session_date']
            session_title = form.cleaned_data['session_title']

            session, created = AttendanceSession.objects.get_or_create(
                course=course,
                session_date=session_date,
                defaults={'title': session_title},
            )

            for student in students:
                field_name = f'student_{student.id}'
                status = form.cleaned_data.get(field_name, 'present')
                AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={'status': status},
                )

            messages.success(
                request,
                f'Attendance for {session_date} saved successfully.'
            )
            return redirect(
                'teacher_panel:attendance_sheet', course_pk=course.pk
            )

        sessions = AttendanceSession.objects.filter(course=course).prefetch_related(
            'records__student'
        ).order_by('-session_date')[:10]

        return render(request, self.template_name, {
            'course': course,
            'form': form,
            'sessions': sessions,
            'students': students,
        })


class TeacherAnalyticsDashboardView(LoginRequiredMixin, TeacherRequiredMixin, TemplateView):
    template_name = 'teacher_panel/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        courses = Course.objects.filter(created_by=user)
        course_ids = courses.values_list('id', flat=True)

        submissions = AssignmentSubmission.objects.filter(
            assignment__module__course__in=course_ids
        )

        total_submissions = submissions.count()
        graded_submissions = submissions.exclude(grade__isnull=True)

        class_avg = graded_submissions.aggregate(
            avg=Coalesce(Avg('grade'), Value(0.0), output_field=DecimalField())
        )['avg']

        total_assignments = Assignment.objects.filter(
            module__course__in=course_ids
        ).count()

        expected_submissions = total_assignments * User.objects.filter(
            role='student'
        ).count()

        submission_rate = 0.0
        if expected_submissions > 0:
            submission_rate = round(
                (total_submissions / expected_submissions) * 100, 1
            )

        student_avg_grades = (
            AssignmentSubmission.objects
            .filter(assignment__module__course__in=course_ids)
            .values('student', 'student__username')
            .annotate(avg_grade=Coalesce(Avg('grade'), Value(0.0), output_field=DecimalField()))
        )

        three_absent_students = (
            AttendanceRecord.objects
            .filter(
                session__course__in=course_ids,
                status='absent',
            )
            .values('student', 'student__username')
            .annotate(absences=Count('id'))
            .filter(absences__gt=3)
            .values_list('student_id', flat=True)
        )

        at_risk_student_ids = set()
        for entry in student_avg_grades:
            if entry['avg_grade'] < 50.0:
                at_risk_student_ids.add(entry['student'])
        at_risk_student_ids.update(three_absent_students)

        at_risk_students = User.objects.filter(
            id__in=at_risk_student_ids, role='student'
        ).annotate(
            avg_grade=Coalesce(
                Avg('assignment_submissions__grade'), Value(0.0),
                output_field=DecimalField(),
            ),
            absence_count=Coalesce(
                Count(
                    'attendance_records',
                    filter=Q(
                        attendance_records__session__course__in=course_ids,
                        attendance_records__status='absent',
                    ),
                ),
                Value(0),
            ),
        ).order_by('avg_grade')

        context['class_average'] = round(class_avg, 2)
        context['submission_rate'] = submission_rate
        context['at_risk_students'] = at_risk_students
        context['total_courses'] = courses.count()
        context['total_submissions'] = total_submissions
        context['graded_submissions'] = graded_submissions.count()
        context['course_list'] = courses

        return context
