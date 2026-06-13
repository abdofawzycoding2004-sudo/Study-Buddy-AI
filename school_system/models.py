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
