from django.db import models
from django.conf import settings


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
            Q(class_teacher=self) | Q(timetableslots__teacher=self)
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
            student=self, status='present'
        ).count()
        return round((present / total) * 100, 2)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class TimetableSlot(models.Model):
    DAY_CHOICES = [
        ('SATURDAY', 'Saturday'),
        ('SUNDAY', 'Sunday'),
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
    ]
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name='timetableslots'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='timetableslots'
    )
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='timetableslots'
    )
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Timetable Slot'
        verbose_name_plural = 'Timetable Slots'

    def __str__(self):
        return (
            f"{self.classroom.name} - {self.subject.name} "
            f"({self.get_day_of_week_display()} {self.start_time}-{self.end_time})"
        )


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='attendance_records'
    )
    timetable_slot = models.ForeignKey(
        TimetableSlot, on_delete=models.CASCADE, related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='marked_attendance'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'timetable_slot', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"
