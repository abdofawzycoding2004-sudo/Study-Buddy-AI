from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children'
    )

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='courses_created',
        limit_choices_to={'role': 'teacher'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses'
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='modules'
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Material(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('video', 'Video Link'),
        ('audio', 'Audio'),
        ('presentation', 'Presentation'),
    ]
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='materials'
    )
    title = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_upload = models.FileField(
        upload_to='materials/', blank=True, null=True
    )
    external_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Assignment(models.Model):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='assignments'
    )
    title = models.CharField(max_length=255)
    instructions = models.TextField()
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField()

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return self.title


class Quiz(models.Model):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='quizzes'
    )
    title = models.CharField(max_length=255)
    time_limit_mins = models.PositiveIntegerField()
    max_attempts = models.PositiveIntegerField()
    randomize_questions = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'quizzes'

    @property
    def total_quiz_points(self):
        return self.questions.aggregate(
            total=models.Sum('points')
        )['total'] or 0

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True / False'),
        ('short_answer', 'Short Answer'),
    ]
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions'
    )
    text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES
    )
    points = models.PositiveIntegerField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='choices'
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='submissions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='assignment_submissions'
    )
    file_upload = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']

    @property
    def is_late(self):
        if self.submitted_at and self.assignment.due_date:
            return self.submitted_at > self.assignment.due_date
        return False

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


class AttendanceSession(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='attendance_sessions'
    )
    session_date = models.DateField()
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.course.title} - {self.title} ({self.session_date})"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    session = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE, related_name='records'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        ordering = ['session', 'student']
        unique_together = ['session', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.session.title}: {self.status}"
