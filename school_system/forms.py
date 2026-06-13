import json
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    School, Grade, ClassRoom, Subject,
    TeacherProfile, StudentProfile, TimetableSlot, LiveClassSession,
    Assessment, Question, AnswerOption, AssessmentSubmission,
    DocumentShare, DocumentCategory,
)

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'البريد الإلكتروني',
            'dir': 'rtl',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور',
            'dir': 'rtl',
        })
    )

    class Meta:
        fields = ['username', 'password']


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@school.edu',
            'dir': 'rtl',
        }),
        help_text='Required. Enter a valid email address.',
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'dir': 'rtl',
        }),
        help_text='Minimum 8 characters.',
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'dir': 'rtl',
        }),
        help_text='Enter the same password as above.',
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الاسم الأول',
            'dir': 'rtl',
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم العائلة',
            'dir': 'rtl',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email


class TeacherRegistrationForm(CustomUserCreationForm):
    employee_id = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., TCH001',
            'dir': 'rtl',
        }),
        help_text='Unique employee identifier.',
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your school.',
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '6',
        }),
        help_text='Select a school first, then choose subjects.',
    )
    qualifications = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Degrees, certifications, etc.',
            'dir': 'rtl',
        })
    )
    experience_years = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
        })
    )
    specialization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Mathematics, Physics',
            'dir': 'rtl',
        })
    )
    office_room = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Room 201',
            'dir': 'rtl',
        })
    )
    hire_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    def clean_subjects(self):
        subjects = self.cleaned_data.get('subjects')
        school = self.cleaned_data.get('school')
        if subjects and school:
            valid = Subject.objects.filter(
                schools=school, pk__in=[s.pk for s in subjects]
            )
            if valid.count() != subjects.count():
                raise ValidationError('All subjects must belong to the selected school.')
        return subjects

    class Meta(CustomUserCreationForm.Meta):
        model = User
        fields = CustomUserCreationForm.Meta.fields + [
            'employee_id', 'school', 'subjects', 'qualifications',
            'experience_years', 'specialization', 'office_room', 'hire_date',
        ]


class StudentRegistrationForm(CustomUserCreationForm):
    student_id = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., STU2025001',
            'dir': 'rtl',
        }),
        help_text='Unique student identifier.',
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your school.',
    )
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your grade.',
    )
    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your class section.',
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    gender = forms.ChoiceField(
        choices=StudentProfile.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    parent_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parent/Guardian full name',
            'dir': 'rtl',
        })
    )
    parent_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+970 5X XXX XXXX',
            'dir': 'rtl',
        })
    )
    parent_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'parent@example.com',
            'dir': 'rtl',
        })
    )
    emergency_contact_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emergency contact full name',
            'dir': 'rtl',
        })
    )
    emergency_contact_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+970 5X XXX XXXX',
            'dir': 'rtl',
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Home address',
            'dir': 'rtl',
        })
    )

    class Meta(CustomUserCreationForm.Meta):
        model = User
        fields = CustomUserCreationForm.Meta.fields + [
            'student_id', 'school', 'grade', 'classroom',
            'date_of_birth', 'gender', 'address',
            'parent_name', 'parent_phone', 'parent_email',
            'emergency_contact_name', 'emergency_contact_phone',
        ]

    def clean_classroom(self):
        classroom = self.cleaned_data.get('classroom')
        grade = self.cleaned_data.get('grade')
        if classroom and grade and classroom.grade != grade:
            raise ValidationError(
                'The selected classroom does not belong to the selected grade.'
            )
        return classroom

    def clean_student_id(self):
        sid = self.cleaned_data.get('student_id')
        if StudentProfile.objects.filter(student_id=sid).exists():
            raise ValidationError('This student ID is already in use.')
        return sid


class TimetableSlotForm(forms.ModelForm):
    class Meta:
        model = TimetableSlot
        fields = [
            'subject', 'classroom', 'day_of_week',
            'start_time', 'end_time', 'room_location',
            'academic_year', 'semester',
        ]
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'step': '1800',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'step': '1800',
            }),
            'room_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Room 101',
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2025-2026',
            }),
            'semester': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not hasattr(field.widget, 'attrs'):
                continue
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        if teacher:
            self.fields['classroom'].queryset = ClassRoom.objects.filter(
                grade__school=teacher.school, is_active=True
            )
            self.fields['subject'].queryset = teacher.subjects.all()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        teacher = cleaned.get('teacher')
        classroom = cleaned.get('classroom')
        day = cleaned.get('day_of_week')
        academic_year = cleaned.get('academic_year')

        if start and end and end <= start:
            raise ValidationError('End time must be after start time.')

        if teacher and day and start and end and academic_year:
            conflicts = TimetableSlot.objects.filter(
                teacher=teacher,
                day_of_week=day,
                academic_year=academic_year,
                is_active=True,
            )
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            for slot in conflicts:
                if start < slot.end_time and slot.start_time < end:
                    raise ValidationError(
                        f'Time conflict with existing slot: {slot}'
                    )

        return cleaned


class LiveClassSessionForm(forms.ModelForm):
    class Meta:
        model = LiveClassSession
        fields = [
            'session_date', 'delivery_type', 'zoom_join_url',
            'meeting_id', 'meeting_password', 'notes',
        ]
        widgets = {
            'session_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'delivery_type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleDeliveryFields()',
            }),
            'zoom_join_url': forms.URLInput(attrs={
                'class': 'form-control online-field',
                'placeholder': 'https://zoom.us/j/...',
            }),
            'meeting_id': forms.TextInput(attrs={
                'class': 'form-control online-field',
                'placeholder': 'Meeting ID',
            }),
            'meeting_password': forms.TextInput(attrs={
                'class': 'form-control online-field',
                'placeholder': 'Meeting password',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Session notes...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['session_date'].initial = timezone.localdate()
        self.fields['zoom_join_url'].required = False
        self.fields['meeting_id'].required = False
        self.fields['meeting_password'].required = False

    def clean_session_date(self):
        date = self.cleaned_data.get('session_date')
        if date and date < timezone.localdate():
            raise ValidationError('Session date cannot be in the past.')
        return date

    def clean(self):
        cleaned = super().clean()
        delivery = cleaned.get('delivery_type')
        zoom_url = cleaned.get('zoom_join_url')

        if delivery == 'ONLINE' and not zoom_url:
            self.add_error('zoom_join_url', 'Join URL is required for online classes.')

        return cleaned


class BulkAttendanceForm(forms.Form):
    session_id = forms.IntegerField(widget=forms.HiddenInput())
    attendance_data = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'd-none'})
    )

    def clean_attendance_data(self):
        data = self.cleaned_data.get('attendance_data')
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError('Invalid JSON format.')
        if not isinstance(parsed, dict):
            raise ValidationError('Expected a JSON object.')
        valid_statuses = ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']
        for key, val in parsed.items():
            if val not in valid_statuses:
                raise ValidationError(f"Invalid status '{val}' for student {key}.")
        return parsed


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = [
            'type', 'title', 'description', 'instructions', 'subject', 'grade',
            'classroom', 'target_students', 'due_date', 'max_points',
            'time_limit_mins', 'allow_late_submission', 'late_penalty_percent',
            'show_correct_answers',
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'dir': 'rtl'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'dir': 'rtl'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'target_students': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '8'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'time_limit_mins': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'allow_late_submission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'late_penalty_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'show_correct_answers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['subject'].queryset = teacher.subjects.all()
            self.fields['grade'].queryset = Grade.objects.filter(
                school=teacher.school, is_active=True
            )
            grade_id = self.data.get('grade') or (
                getattr(self.instance, 'grade_id', None) if self.instance.pk else None
            )
            if grade_id:
                try:
                    grade = Grade.objects.get(pk=grade_id)
                    self.fields['classroom'].queryset = grade.classes.filter(is_active=True)
                except (Grade.DoesNotExist, ValueError, OverflowError):
                    self.fields['classroom'].queryset = ClassRoom.objects.none()
            else:
                self.fields['classroom'].queryset = ClassRoom.objects.none()
            classroom_id = self.data.get('classroom') or (
                getattr(self.instance, 'classroom_id', None) if self.instance.pk else None
            )
            if classroom_id:
                try:
                    classroom = ClassRoom.objects.get(pk=classroom_id)
                    self.fields['target_students'].queryset = classroom.students.all()
                except (ClassRoom.DoesNotExist, ValueError, OverflowError):
                    self.fields['target_students'].queryset = StudentProfile.objects.none()
            else:
                self.fields['target_students'].queryset = StudentProfile.objects.none()
        self.fields['target_students'].required = False
        self.fields['time_limit_mins'].required = False

    def clean(self):
        cleaned = super().clean()
        due = cleaned.get('due_date')
        if due and due <= timezone.now():
            raise ValidationError('Due date must be in the future.')
        asst_type = cleaned.get('type')
        time_limit = cleaned.get('time_limit_mins')
        if asst_type == 'QUIZ' and not time_limit:
            self.add_error('time_limit_mins', 'Time limit is required for quizzes.')
        return cleaned


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'question_text', 'correct_answer', 'explanation', 'points', 'order', 'required']
        widgets = {
            'question_type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleQuestionFields()',
            }),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'dir': 'rtl',
            }),
            'correct_answer': forms.TextInput(attrs={
                'class': 'form-control', 'dir': 'rtl',
                'placeholder': 'Correct answer (for Short Answer type)',
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'dir': 'rtl',
            }),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_points(self):
        pts = self.cleaned_data.get('points')
        if pts and pts < 1:
            raise ValidationError('Points must be at least 1.')
        return pts


class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['option_text', 'is_correct', 'order']
        widgets = {
            'option_text': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


AnswerOptionFormSet = forms.inlineformset_factory(
    Question, AnswerOption, form=AnswerOptionForm,
    extra=4, max_num=6, min_num=2,
    validate_min=True, can_delete=True,
)


class SubmissionReviewForm(forms.Form):
    final_score = forms.DecimalField(
        max_digits=5, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.25',
        }),
    )
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4, 'dir': 'rtl',
        }),
    )
    is_verified = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Verify grade (teacher override)',
    )


class StudentAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', [])
        super().__init__(*args, **kwargs)
        for q in questions:
            field_name = f'question_{q.pk}'
            if q.question_type == 'MCQ':
                choices = [(o.pk, o.option_text) for o in q.options.all()]
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    label=q.question_text,
                    required=q.required,
                )
            elif q.question_type == 'TRUE_FALSE':
                choices = [('True', 'True'), ('False', 'False')]
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    label=q.question_text,
                    required=q.required,
                )
            elif q.question_type == 'SHORT_ANSWER':
                self.fields[field_name] = forms.CharField(
                    widget=forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
                    label=q.question_text,
                    required=q.required,
                )
            elif q.question_type == 'ESSAY':
                self.fields[field_name] = forms.CharField(
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'dir': 'rtl'}),
                    label=q.question_text,
                    required=q.required,
                )
            self.fields[field_name].question_obj = q


class DocumentShareForm(forms.ModelForm):
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='الصف الدراسي',
    )

    class Meta:
        model = DocumentShare
        fields = [
            'title', 'description', 'file_upload', 'category', 'subject',
            'is_public', 'allowed_classes', 'allowed_students', 'expires_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'dir': 'rtl'}),
            'file_upload': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,'
                         '.jpg,.jpeg,.png,.gif,.bmp,.webp,.svg,'
                         '.mp4,.avi,.mkv,.mov,.wmv,.webm,'
                         '.mp3,.wav,.ogg,.aac,.flac,.wma',
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleVisibilityFields()',
            }),
            'allowed_classes': forms.SelectMultiple(attrs={
                'class': 'form-control', 'size': '6',
            }),
            'allowed_students': forms.SelectMultiple(attrs={
                'class': 'form-control', 'size': '6',
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local',
            }),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['subject'].queryset = teacher.subjects.all()
            self.fields['category'].queryset = DocumentCategory.objects.all()
            self.fields['grade'].queryset = Grade.objects.filter(
                school=teacher.school, is_active=True
            )
            grade_id = self.data.get('grade')
            if grade_id:
                try:
                    grade = Grade.objects.get(pk=grade_id)
                    self.fields['allowed_classes'].queryset = grade.classes.filter(
                        is_active=True
                    )
                except (Grade.DoesNotExist, ValueError, OverflowError):
                    self.fields['allowed_classes'].queryset = ClassRoom.objects.none()
            else:
                self.fields['allowed_classes'].queryset = ClassRoom.objects.none()
            classroom_ids = self.data.getlist('allowed_classes')
            if classroom_ids:
                self.fields['allowed_students'].queryset = StudentProfile.objects.filter(
                    classroom_id__in=classroom_ids
                )
            else:
                self.fields['allowed_students'].queryset = StudentProfile.objects.none()
        self.fields['allowed_classes'].required = False
        self.fields['allowed_students'].required = False
        self.fields['expires_at'].required = False

    def clean_file_upload(self):
        file = self.cleaned_data.get('file_upload')
        if not file:
            return file
        self.instance.file_size = file.size
        from .utils import validate_file_upload
        validate_file_upload(file)
        return file

    def clean(self):
        cleaned = super().clean()
        is_public = cleaned.get('is_public')
        allowed_classes = cleaned.get('allowed_classes')
        allowed_students = cleaned.get('allowed_students')
        if is_public and not allowed_classes and not allowed_students:
            raise ValidationError(
                'Select at least one class or student for a public document.'
            )
        return cleaned
