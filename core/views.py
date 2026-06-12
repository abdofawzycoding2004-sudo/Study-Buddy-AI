from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import TeacherRegistrationForm, StudentRegistrationForm


def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')
    return redirect('login')


def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'تم إنشاء الحساب بنجاح')
            return redirect('teacher_dashboard')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'register.html', {'form': form, 'role': 'teacher'})


def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'تم إنشاء الحساب بنجاح')
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'register.html', {'form': form, 'role': 'student'})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'teacher':
                return redirect('teacher_dashboard')
            return redirect('student_dashboard')
        messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html', {'user': request.user})


@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html', {'user': request.user})
