import json
import re
from collections import Counter
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib import messages
from django.http import StreamingHttpResponse, JsonResponse
from django.db.models import Count, Avg
from .models import Document, ChatMessage, QuizAttempt
from .utils import extract_text, chunk_text, store_document_chunks, query_similar_chunks, ask_llm_stream, generate_quiz, grade_short_answer
from school_system.forms import TeacherRegistrationForm, StudentRegistrationForm
from school_system.models import TeacherProfile, StudentProfile


def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')
    return redirect('login')


@ensure_csrf_cookie
def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'teacher'
            user.save()
            TeacherProfile.objects.create(
                user=user,
                employee_id=form.cleaned_data['employee_id'],
                school=form.cleaned_data['school'],
                qualifications=form.cleaned_data['qualifications'],
                experience_years=form.cleaned_data['experience_years'],
                specialization=form.cleaned_data.get('specialization', ''),
                office_room=form.cleaned_data.get('office_room', ''),
                hire_date=form.cleaned_data['hire_date'],
            )
            tp = TeacherProfile.objects.get(user=user)
            tp.subjects.set(form.cleaned_data['subjects'])
            login(request, user)
            messages.success(request, 'تم إنشاء الحساب بنجاح')
            return redirect('teacher_dashboard')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'registration/teacher_register.html', {'form': form})


@ensure_csrf_cookie
def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.save()
            classroom = form.cleaned_data['classroom']
            StudentProfile.objects.create(
                user=user,
                student_id=form.cleaned_data['student_id'],
                school=form.cleaned_data['school'],
                classroom=classroom,
                grade=form.cleaned_data['grade'],
                date_of_birth=form.cleaned_data['date_of_birth'],
                gender=form.cleaned_data['gender'],
                address=form.cleaned_data.get('address', ''),
                parent_name=form.cleaned_data['parent_name'],
                parent_phone=form.cleaned_data['parent_phone'],
                parent_email=form.cleaned_data.get('parent_email', ''),
                emergency_contact_name=form.cleaned_data['emergency_contact_name'],
                emergency_contact_phone=form.cleaned_data['emergency_contact_phone'],
            )
            classroom.current_enrollment += 1
            classroom.save()
            login(request, user)
            messages.success(request, 'تم إنشاء الحساب بنجاح')
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'registration/student_register.html', {'form': form})


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if request.user.role == 'teacher':
                return redirect('teacher_dashboard')
            return redirect('student_dashboard')
        messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    else:
        form = LoginForm(request)
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def upload_document(request):
    if request.method == 'POST' and request.user.role == 'teacher':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        if title and file:
            doc = Document.objects.create(
                teacher=request.user,
                title=title,
                file=file,
            )
            try:
                text = extract_text(doc.file.path)
                chunks = chunk_text(text)
                chunk_count = store_document_chunks(doc, chunks)
                doc.is_processed = True
                doc.chunk_count = chunk_count
                doc.save()
                messages.success(request, f'تم رفع "{title}" ومعالجته بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء المعالجة: {e}')
        else:
            messages.error(request, 'يرجى إدخال العنوان ورفع ملف')
        return redirect('teacher_dashboard')
    return redirect('teacher_dashboard')


@login_required
@ensure_csrf_cookie
def teacher_dashboard(request):
    documents = Document.objects.filter(teacher=request.user).order_by('-uploaded_at')

    students_data = (ChatMessage.objects.values('student__username')
                     .annotate(total_questions=Count('id'))
                     .order_by('-total_questions'))

    quiz_data = (QuizAttempt.objects.values('student__username')
                 .annotate(avg_score=Avg('score'), total_attempts=Count('id'))
                 .order_by('-avg_score'))

    all_questions = ChatMessage.objects.values_list('question', flat=True)
    stop_words = {'what', 'is', 'the', 'of', 'in', 'to', 'a', 'for', 'on', 'and', 'does', 'are', 'do', 'how', 'why', 'can', 'you', 'this', 'that', 'with', 'it', 'an', 'or', 'if', 'be', 'from', 'by', 'at', 'as', 'which', 'when', 'where', 'who', 'was', 'were', 'has', 'have', 'had', 'not', 'no', 'but', 'so', 'all', 'each', 'any', 'main', 'called', 'explain', 'describe', 'whats', 'give', 'list', 'name', 'من', 'ما', 'هو', 'في', 'ل', 'على', 'و', 'هل', 'اذكر', 'ما هو', 'شرح'}
    words = []
    for q in all_questions:
        tokens = re.findall(r'\w+', q.lower())
        words.extend([w for w in tokens if w not in stop_words and len(w) > 2])
    topic_counts = Counter(words).most_common(8)
    topics = [{'topic': t[0], 'count': t[1]} for t in topic_counts]

    return render(request, 'teacher_dashboard.html', {
        'user': request.user,
        'documents': documents,
        'students_data': students_data,
        'quiz_data': quiz_data,
        'topics': topics,
    })


@csrf_exempt
def chat_api(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return StreamingHttpResponse(
            'data: {"error": "Unauthorized"}\n\n',
            content_type='text/event-stream',
        )
    if request.method != 'POST':
        return StreamingHttpResponse(
            'data: {"error": "Use POST"}\n\n',
            content_type='text/event-stream',
        )
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    if not question:
        return StreamingHttpResponse(
            'data: {"error": "Question is required"}\n\n',
            content_type='text/event-stream',
        )

    chunks = query_similar_chunks(question)
    user = request.user

    def event_stream():
        full_answer = ""
        try:
            for token in ask_llm_stream(question, chunks):
                full_answer += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        ChatMessage.objects.create(
            student=user,
            question=question,
            answer=full_answer,
        )

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


@csrf_exempt
def generate_quiz_view(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Use POST'}, status=405)
    data = json.loads(request.body)
    num_questions = int(data.get('num_questions', 5))
    difficulty = data.get('difficulty', 'medium')
    question_type = data.get('question_type', 'multiple_choice')

    chunks = query_similar_chunks('curriculum content', n_results=5)

    try:
        questions = generate_quiz(num_questions, difficulty, question_type, chunks if chunks else None)
        return JsonResponse({'questions': questions})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def grade_short_answer_view(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Use POST'}, status=405)
    data = json.loads(request.body)
    result = grade_short_answer(
        data['question'],
        data['correct_answer'],
        data['student_answer'],
    )
    return JsonResponse(result)


@csrf_exempt
def save_quiz_result(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Use POST'}, status=405)
    data = json.loads(request.body)
    QuizAttempt.objects.create(
        student=request.user,
        score=int(data['score']),
        total=int(data['total']),
    )
    return JsonResponse({'ok': True})


@login_required
@ensure_csrf_cookie
def student_dashboard(request):
    history = ChatMessage.objects.filter(student=request.user)[:10]
    return render(request, 'student_dashboard.html', {
        'user': request.user,
        'history': history,
    })
