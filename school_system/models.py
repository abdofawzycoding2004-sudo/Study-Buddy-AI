import os
import mimetypes
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class School(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Palestine')
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    config_payload = models.JSONField(default=dict)
    established_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class Grade(models.Model):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='grades'
    )
    name = models.CharField(max_length=50)
    grade_level = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    academic_year = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['school', 'name', 'academic_year']
        ordering = ['grade_level']

    def __str__(self):
        return f"{self.school.code} - {self.name}"


class Subject(models.Model):
    CATEGORY_CHOICES = [
        ('SCIENCE', 'Science'),
        ('MATH', 'Mathematics'),
        ('LANGUAGE', 'Language'),
        ('SOCIAL_STUDIES', 'Social Studies'),
        ('ART', 'Art'),
        ('SPORTS', 'Sports'),
        ('OTHER', 'Other'),
    ]
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    schools = models.ManyToManyField(School, related_name='subjects')
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    is_core_subject = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    employee_id = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='teachers'
    )
    subjects = models.ManyToManyField(Subject, related_name='teachers')
    classes = models.ManyToManyField(
        'ClassRoom', blank=True, related_name='assigned_teachers'
    )
    qualifications = models.TextField()
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=100, blank=True)
    office_room = models.CharField(max_length=50, blank=True)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    def get_assigned_classes(self):
        from django.db.models import Q
        return ClassRoom.objects.filter(
            Q(class_teacher=self) | Q(timetable_slots__teacher=self) | Q(assigned_teachers=self)
        ).distinct()

    def get_total_students(self):
        assigned_classes = self.get_assigned_classes()
        return StudentProfile.objects.filter(
            classroom__in=assigned_classes
        ).count()

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class ClassRoom(models.Model):
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name='classes'
    )
    name = models.CharField(max_length=50)
    room_number = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=30)
    current_enrollment = models.PositiveIntegerField(default=0)
    class_teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_classes'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['grade', 'name']
        ordering = ['grade__grade_level', 'name']

    def get_students(self):
        return StudentProfile.objects.filter(classroom=self)

    def get_teachers(self):
        from django.db.models import Q
        teacher_ids = TimetableSlot.objects.filter(
            classroom=self
        ).values_list('teacher_id', flat=True).distinct()
        teachers = TeacherProfile.objects.filter(
            Q(id__in=teacher_ids) | Q(managed_classes=self)
        ).distinct()
        return teachers

    def __str__(self):
        return f"{self.grade.name} - {self.name}"


class StudentProfile(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='students'
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name='students'
    )
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name='students'
    )
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.TextField(blank=True)
    parent_name = models.CharField(max_length=200)
    parent_phone = models.CharField(max_length=15)
    parent_email = models.EmailField(blank=True)
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=15)
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def class_name(self):
        return self.classroom.name

    def get_timetable(self):
        return TimetableSlot.objects.filter(classroom=self.classroom)

    def get_attendance_percentage(self):
        total = AttendanceRecord.objects.filter(student=self).count()
        if total == 0:
            return 100.0
        present = AttendanceRecord.objects.filter(
            student=self, status='PRESENT'
        ).count()
        return round((present / total) * 100, 2)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class TimetableSlot(models.Model):
    DAY_CHOICES = [
        (0, 'Saturday'),
        (1, 'Sunday'),
        (2, 'Monday'),
        (3, 'Tuesday'),
        (4, 'Wednesday'),
        (5, 'Thursday'),
        (6, 'Friday'),
    ]
    DAY_NAMES = {k: v for k, v in DAY_CHOICES}

    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='timetable_slots'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='timetable_slots'
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name='timetable_slots'
    )
    day_of_week = models.PositiveIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_mins = models.PositiveIntegerField(editable=False)
    room_location = models.CharField(max_length=100, blank=True)
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(
        max_length=20,
        choices=[('FALL', 'Fall'), ('SPRING', 'Spring')],
        default='FALL',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['teacher', 'classroom', 'day_of_week', 'start_time', 'academic_year']
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Timetable Slot'
        verbose_name_plural = 'Timetable Slots'

    def __str__(self):
        day_name = self.DAY_NAMES.get(self.day_of_week, 'Unknown')
        return (
            f"{self.teacher} - {self.subject} - {self.classroom} "
            f"({day_name} {self.start_time})"
        )

    def clean(self):
        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                raise ValidationError('End time must be after start time.')
            delta = timedelta(
                hours=self.end_time.hour - self.start_time.hour,
                minutes=self.end_time.minute - self.start_time.minute,
            )
            self.duration_mins = int(delta.total_seconds() // 60)

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = timedelta(
                hours=self.end_time.hour - self.start_time.hour,
                minutes=self.end_time.minute - self.start_time.minute,
            )
            self.duration_mins = int(delta.total_seconds() // 60)
        super().save(*args, **kwargs)

    @property
    def duration_formatted(self):
        hours = self.duration_mins // 60
        mins = self.duration_mins % 60
        if hours and mins:
            return f"{hours}h {mins}m"
        elif hours:
            return f"{hours}h"
        return f"{mins}m"

    def get_students(self):
        return StudentProfile.objects.filter(classroom=self.classroom)

    def conflicts_with(self, other):
        if self.day_of_week != other.day_of_week:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time


class LiveClassSession(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    DELIVERY_CHOICES = [
        ('ON_CAMPUS', 'On Campus'),
        ('ONLINE', 'Online'),
    ]

    timetable_slot = models.ForeignKey(
        TimetableSlot, on_delete=models.CASCADE, related_name='live_sessions'
    )
    session_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT'
    )
    delivery_type = models.CharField(
        max_length=20, choices=DELIVERY_CHOICES, default='ON_CAMPUS'
    )
    zoom_join_url = models.URLField(blank=True, null=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    meeting_password = models.CharField(max_length=50, blank=True, null=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    duration_actual_mins = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recording_url = models.URLField(blank=True, null=True)
    attendance_taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['timetable_slot', 'session_date']
        ordering = ['-session_date', '-created_at']

    def __str__(self):
        return f"{self.timetable_slot} - {self.session_date} ({self.get_status_display()})"

    @property
    def start_time(self):
        return self.timetable_slot.start_time

    @property
    def end_time(self):
        return self.timetable_slot.end_time

    @property
    def subject(self):
        return self.timetable_slot.subject

    @property
    def classroom(self):
        return self.timetable_slot.classroom

    @property
    def teacher(self):
        return self.timetable_slot.teacher

    @property
    def is_upcoming(self):
        return self.status == 'CONFIRMED' and self.session_date >= timezone.localdate()

    @property
    def is_active_session(self):
        return self.status == 'IN_PROGRESS'

    def confirm(self):
        self.status = 'CONFIRMED'
        self.save(update_fields=['status', 'updated_at'])

    def start(self):
        self.status = 'IN_PROGRESS'
        self.start_datetime = timezone.now()
        self.save(update_fields=['status', 'start_datetime', 'updated_at'])

    def complete(self):
        self.status = 'COMPLETED'
        self.end_datetime = timezone.now()
        if self.start_datetime:
            delta = self.end_datetime - self.start_datetime
            self.duration_actual_mins = int(delta.total_seconds() // 60)
        self.save(update_fields=['status', 'end_datetime', 'duration_actual_mins', 'updated_at'])

    def cancel(self):
        self.status = 'CANCELLED'
        self.save(update_fields=['status', 'updated_at'])

    def get_attendance_records(self):
        return self.attendance_logs.select_related('student__user').all()

    def get_student_count(self):
        return StudentProfile.objects.filter(classroom=self.classroom).count()

    def get_present_count(self):
        return self.attendance_logs.filter(status='PRESENT').count()

    def get_attendance_percentage(self):
        total = self.get_student_count()
        if total == 0:
            return 0.0
        present = self.get_present_count()
        return round((present / total) * 100, 2)


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]

    session = models.ForeignKey(
        LiveClassSession, on_delete=models.CASCADE, related_name='attendance_logs'
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='attendance_records'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['session', 'student']
        ordering = ['student__user__first_name', 'student__user__last_name']

    def clean(self):
        if self.student and self.session and self.student.classroom != self.session.classroom:
            raise ValidationError(
                f"{self.student} is not enrolled in {self.session.classroom}."
            )

    def __str__(self):
        return f"{self.student} - {self.session} - {self.get_status_display()}"


class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('QUIZ', 'Quiz'),
        ('HOMEWORK', 'Homework'),
    ]

    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='assessments'
    )
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name='assessments'
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name='assessments',
        null=True, blank=True,
    )
    target_students = models.ManyToManyField(
        StudentProfile, blank=True, related_name='targeted_assessments'
    )
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='assessments'
    )
    due_date = models.DateTimeField()
    available_from = models.DateTimeField(auto_now_add=True)
    max_points = models.PositiveIntegerField(default=100)
    time_limit_mins = models.PositiveIntegerField(null=True, blank=True)
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.PositiveIntegerField(default=10)
    show_correct_answers = models.BooleanField(default=True)
    show_correct_answers_after = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date']

    @property
    def is_active(self):
        now = timezone.now()
        return self.is_published and now >= self.available_from

    @property
    def is_overdue(self):
        return timezone.now() > self.due_date

    @property
    def submission_count(self):
        return self.submissions.count()

    def get_target_students(self):
        if self.target_students.exists():
            return self.target_students.all()
        return StudentProfile.objects.filter(classroom=self.classroom)

    def is_target_student(self, student):
        if self.target_students.exists():
            return self.target_students.filter(pk=student.pk).exists()
        return student.classroom == self.classroom

    def calculate_late_penalty(self, submission):
        if not submission.is_late:
            return 0
        days_late = (submission.submitted_at - self.due_date).days
        return min(days_late * self.late_penalty_percent, 100)

    def publish(self):
        self.is_published = True
        self.save(update_fields=['is_published', 'updated_at'])

    def unpublish(self):
        self.is_published = False
        self.save(update_fields=['is_published', 'updated_at'])

    def __str__(self):
        return f"{self.get_type_display()} - {self.title} ({self.classroom})"


class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice'),
        ('TRUE_FALSE', 'True/False'),
        ('SHORT_ANSWER', 'Short Answer'),
        ('ESSAY', 'Essay'),
    ]

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name='questions'
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    correct_answer = models.TextField(blank=True, help_text='Expected answer for Short Answer type')
    required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    @property
    def is_auto_gradable(self):
        return self.question_type in ['MCQ', 'TRUE_FALSE', 'SHORT_ANSWER']

    def __str__(self):
        return f"{self.get_question_type_display()} - {self.question_text[:50]}"


class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='options'
    )
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.option_text[:50]} ({'Correct' if self.is_correct else 'Incorrect'})"


class AssessmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name='submissions'
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='submissions'
    )
    submitted_answers = models.JSONField(default=dict)
    file_attachment = models.FileField(
        upload_to='submissions/', blank=True, null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auto_calculated_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    teacher_final_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    penalty_applied = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    final_grade_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    feedback = models.TextField(blank=True)
    is_graded = models.BooleanField(default=False)
    is_verified_by_teacher = models.BooleanField(default=False)
    graded_at = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['assignment', 'student', 'attempt_number']

    @property
    def score(self):
        return self.teacher_final_score or self.auto_calculated_score

    @property
    def is_submitted(self):
        return bool(self.submitted_answers) or bool(self.file_attachment)

    @property
    def is_complete(self):
        required = self.assignment.questions.filter(required=True)
        if not self.submitted_answers:
            return False
        return all(str(q.pk) in self.submitted_answers for q in required)

    @property
    def grade_letter(self):
        pct = self.final_grade_percentage
        if pct is None:
            if self.score and self.assignment.max_points:
                pct = (self.score / self.assignment.max_points) * 100
            else:
                return '—'
        if pct >= 90:
            return 'A'
        elif pct >= 80:
            return 'B'
        elif pct >= 70:
            return 'C'
        elif pct >= 60:
            return 'D'
        return 'F'

    def auto_grade(self):
        total_earned = 0
        questions = self.assignment.questions.prefetch_related('options').all()
        for q in questions:
            if not q.is_auto_gradable:
                continue
            ans = self.submitted_answers.get(str(q.pk))
            if ans is None:
                continue
            if q.question_type == 'MCQ':
                correct = q.options.filter(is_correct=True).values_list('id', flat=True)
                if int(ans) in correct:
                    total_earned += q.points
            elif q.question_type == 'TRUE_FALSE':
                correct = q.options.filter(is_correct=True).first()
                if correct and ans == correct.option_text:
                    total_earned += q.points
        self.auto_calculated_score = total_earned
        self.is_graded = True
        self.save(update_fields=['auto_calculated_score', 'is_graded', 'updated_at'])

    def submit(self, answers):
        self.submitted_answers = answers
        if self.assignment.is_overdue:
            self.is_late = True
            penalty = self.assignment.calculate_late_penalty(self)
            self.penalty_applied = penalty
        self.save(update_fields=[
            'submitted_answers', 'is_late', 'penalty_applied', 'updated_at'
        ])
        self.auto_grade()

    def mark_as_graded(self, score, feedback, teacher_override=False):
        self.teacher_final_score = score
        self.feedback = feedback
        self.graded_at = timezone.now()
        if teacher_override:
            self.is_verified_by_teacher = True
        self.is_graded = True
        self.final_grade_percentage = (
            (score / self.assignment.max_points) * 100
            if self.assignment.max_points else 0
        )
        self.save(update_fields=[
            'teacher_final_score', 'feedback', 'graded_at',
            'is_verified_by_teacher', 'is_graded', 'final_grade_percentage',
            'updated_at',
        ])

    def calculate_percentage(self):
        if self.score and self.assignment.max_points:
            return round((self.score / self.assignment.max_points) * 100, 2)
        return 0

    def __str__(self):
        score = self.teacher_final_score or self.auto_calculated_score
        return f"{self.student} - {self.assignment} (Score: {score or 'Pending'})"


class StudentAnswer(models.Model):
    submission = models.ForeignKey(
        AssessmentSubmission, on_delete=models.CASCADE,
        related_name='student_answers'
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='student_answers'
    )
    answer_text = models.TextField(blank=True)
    selected_option = models.ForeignKey(
        AnswerOption, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    teacher_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['submission', 'question']

    def __str__(self):
        return f"{self.question} - {self.answer_text[:50]}"


class DocumentCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#4F46E5')
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class DocumentShare(models.Model):
    FILE_TYPE_CHOICES = [
        ('DOCUMENT', 'Document'),
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_upload = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text='File size in bytes')
    mime_type = models.CharField(max_length=100)
    category = models.ForeignKey(
        DocumentCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents',
    )
    owner_teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='shared_documents',
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents',
    )
    is_public = models.BooleanField(default=False)
    allowed_classes = models.ManyToManyField(
        ClassRoom, blank=True, related_name='shared_documents',
    )
    allowed_students = models.ManyToManyField(
        StudentProfile, blank=True, related_name='shared_documents',
    )
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return f"{self.title} ({self.owner_teacher})"

    def clean(self):
        max_bytes = getattr(settings, 'MAX_UPLOAD_SIZE', 100 * 1024 * 1024)
        if self.file_size > max_bytes:
            raise ValidationError(f'File size exceeds maximum allowed ({max_bytes // (1024*1024)}MB).')

    @property
    def is_accessible(self):
        return self.is_active and (self.expires_at is None or self.expires_at > timezone.now())

    @property
    def file_size_mb(self):
        return self.file_size / (1024 * 1024)

    @property
    def file_extension(self):
        _, ext = os.path.splitext(self.file_upload.name)
        return ext.lower()

    def can_access(self, user):
        if hasattr(user, 'teacher_profile') and user.teacher_profile == self.owner_teacher:
            return True
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if not self.is_accessible:
                return False
            if self.allowed_students.filter(pk=student.pk).exists():
                return True
            if student.classroom and self.allowed_classes.filter(pk=student.classroom.pk).exists():
                return True
        return False

    def increment_download(self):
        DocumentShare.objects.filter(pk=self.pk).update(download_count=models.F('download_count') + 1)
        self.refresh_from_db(fields=['download_count'])

    def increment_view(self):
        DocumentShare.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active'])


class DocumentAccessLog(models.Model):
    ACTION_CHOICES = [
        ('VIEW', 'Viewed'),
        ('DOWNLOAD', 'Downloaded'),
    ]

    document = models.ForeignKey(
        DocumentShare, on_delete=models.CASCADE, related_name='access_logs',
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='document_access_logs',
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['document', 'accessed_at']),
        ]

    def __str__(self):
        return f"{self.student} - {self.document} - {self.action}"
