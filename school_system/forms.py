from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import (
    School, Grade, ClassRoom, Subject,
    TeacherProfile, StudentProfile,
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
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '6',
        }),
        help_text='Hold Ctrl/Cmd to select multiple.',
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



