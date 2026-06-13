import os
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from .models import (
    AssessmentSubmission, Question,
    AttendanceRecord, Assessment, LiveClassSession, DocumentShare,
    StudentProfile,
)


class AutoGradingEngine:

    @staticmethod
    def grade_mcq(submission):
        questions = submission.assignment.questions.filter(
            question_type='MCQ'
        ).prefetch_related('options')
        total = 0
        for q in questions:
            ans = submission.submitted_answers.get(str(q.pk))
            if ans is None:
                continue
            correct_ids = set(
                q.options.filter(is_correct=True).values_list('id', flat=True)
            )
            if int(ans) in correct_ids:
                total += q.points
        return total

    @staticmethod
    def grade_true_false(submission):
        questions = submission.assignment.questions.filter(
            question_type='TRUE_FALSE'
        ).prefetch_related('options')
        total = 0
        for q in questions:
            ans = submission.submitted_answers.get(str(q.pk))
            if ans is None:
                continue
            correct = q.options.filter(is_correct=True).first()
            if correct and ans == correct.option_text:
                total += q.points
        return total

    @staticmethod
    def grade_short_answer(submission):
        questions = submission.assignment.questions.filter(
            question_type='SHORT_ANSWER'
        )
        total = 0
        for q in questions:
            ans = submission.submitted_answers.get(str(q.pk))
            if ans is None or not q.correct_answer:
                continue
            if ans.strip().casefold() == q.correct_answer.strip().casefold():
                total += q.points
        return total

    @staticmethod
    def calculate_total_score(submission):
        mcq = AutoGradingEngine.grade_mcq(submission)
        tf = AutoGradingEngine.grade_true_false(submission)
        sa = AutoGradingEngine.grade_short_answer(submission)
        return mcq + tf + sa

    @staticmethod
    def apply_late_penalty(submission):
        if not submission.is_late:
            return Decimal('0')
        return submission.assignment.calculate_late_penalty(submission)

    @staticmethod
    def generate_feedback(submission):
        score = submission.score or 0
        max_pts = submission.assignment.max_points
        pct = (score / max_pts * 100) if max_pts else 0

        if pct >= 90:
            return 'Excellent work! Outstanding understanding of the material.'
        elif pct >= 80:
            return 'Good job! Strong understanding with minor areas for improvement.'
        elif pct >= 70:
            return 'Satisfactory. Review the questions you missed for better understanding.'
        elif pct >= 60:
            return 'Needs improvement. Consider reviewing the material and asking for help.'
        return 'Significant gaps in understanding. Please seek additional support.'


class AssessmentStatistics:

    @staticmethod
    def get_class_average(assessment):
        subs = AssessmentSubmission.objects.filter(
            assignment=assessment,
            is_graded=True,
        )
        result = subs.aggregate(avg=Avg('auto_calculated_score'))
        return round(result['avg'], 2) if result['avg'] else 0

    @staticmethod
    def get_submission_rate(assessment):
        total = assessment.get_target_students().count()
        if total == 0:
            return 0
        submitted = assessment.submissions.count()
        return round((submitted / total) * 100, 1)

    @staticmethod
    def get_question_difficulty(question):
        subs = AssessmentSubmission.objects.filter(
            assignment=question.assessment,
            is_graded=True,
        )
        if not subs.exists():
            return 0
        correct = 0
        for s in subs:
            ans = s.submitted_answers.get(str(question.pk))
            if ans is None:
                continue
            if question.question_type == 'MCQ':
                correct_ids = set(
                    question.options.filter(
                        is_correct=True
                    ).values_list('id', flat=True)
                )
                if int(ans) in correct_ids:
                    correct += 1
            elif question.question_type == 'TRUE_FALSE':
                correct_opt = question.options.filter(is_correct=True).first()
                if correct_opt and ans == correct_opt.option_text:
                    correct += 1
            elif question.question_type == 'SHORT_ANSWER':
                if question.correct_answer and ans.strip().casefold() == question.correct_answer.strip().casefold():
                    correct += 1
        return round((correct / subs.count()) * 100, 1)

    @staticmethod
    def get_student_performance(student):
        subs = AssessmentSubmission.objects.filter(student=student, is_graded=True)
        result = subs.aggregate(avg=Avg('auto_calculated_score'))
        return round(result['avg'], 2) if result['avg'] else 0


ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',
    'mp4', 'avi', 'mkv', 'mov', 'wmv', 'webm',
    'mp3', 'wav', 'ogg', 'aac', 'flac', 'wma',
}
MAX_UPLOAD_SIZE_MB = 100
MIME_TYPE_MAP = {
    'application/pdf': 'DOCUMENT',
    'application/msword': 'DOCUMENT',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCUMENT',
    'application/vnd.ms-excel': 'DOCUMENT',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'DOCUMENT',
    'application/vnd.ms-powerpoint': 'DOCUMENT',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'DOCUMENT',
    'text/plain': 'DOCUMENT',
    'text/csv': 'DOCUMENT',
    'image/jpeg': 'IMAGE',
    'image/png': 'IMAGE',
    'image/gif': 'IMAGE',
    'image/bmp': 'IMAGE',
    'image/webp': 'IMAGE',
    'image/svg+xml': 'IMAGE',
    'video/mp4': 'VIDEO',
    'video/x-msvideo': 'VIDEO',
    'video/x-matroska': 'VIDEO',
    'video/quicktime': 'VIDEO',
    'video/x-ms-wmv': 'VIDEO',
    'video/webm': 'VIDEO',
    'audio/mpeg': 'AUDIO',
    'audio/wav': 'AUDIO',
    'audio/ogg': 'AUDIO',
    'audio/aac': 'AUDIO',
    'audio/flac': 'AUDIO',
    'audio/x-ms-wma': 'AUDIO',
}


def get_file_type(mime_type, filename):
    result = MIME_TYPE_MAP.get(mime_type)
    if result:
        return result
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    if ext in {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'}:
        return 'DOCUMENT'
    if ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}:
        return 'IMAGE'
    if ext in {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'webm'}:
        return 'VIDEO'
    if ext in {'mp3', 'wav', 'ogg', 'aac', 'flac', 'wma'}:
        return 'AUDIO'
    return 'DOCUMENT'


def validate_file_upload(file, max_size_mb=MAX_UPLOAD_SIZE_MB):
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'File size exceeds {max_size_mb}MB limit.')
    ext = os.path.splitext(file.name)[1].lower().lstrip('.')
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f'File type .{ext} is not allowed.')


def generate_unique_filename(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}_{timezone.now().strftime('%Y%m%d%H%M%S')}{ext}"
    return os.path.join('documents', timezone.now().strftime('%Y/%m/%d'), safe_name)


# ─────────────────────── ANALYTICS ENGINE ───────────────────────

class ClassAnalytics:

    @staticmethod
    def get_average_grade(classroom):
        subs = AssessmentSubmission.objects.filter(
            assignment__classroom=classroom, is_graded=True,
        )
        result = subs.aggregate(avg=Avg('auto_calculated_score'))
        return round(result['avg'], 2) if result['avg'] else 0

    @staticmethod
    def get_attendance_rate(classroom, days=30):
        cutoff = timezone.now() - timedelta(days=days)
        records = AttendanceRecord.objects.filter(
            student__classroom=classroom,
            session__session_date__gte=cutoff,
        )
        total = records.count()
        if total == 0:
            return 0
        present = records.filter(status__in=['PRESENT', 'LATE']).count()
        return round((present / total) * 100, 1)

    @staticmethod
    def get_top_performers(classroom, limit=5):
        students = StudentProfile.objects.filter(classroom=classroom)
        results = []
        for s in students:
            avg = StudentAnalytics.get_overall_average(s)
            results.append((s, avg))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    @staticmethod
    def get_struggling_students(classroom, threshold=50):
        students = StudentProfile.objects.filter(classroom=classroom)
        struggling = []
        for s in students:
            avg = StudentAnalytics.get_overall_average(s)
            attendance = StudentAnalytics.get_attendance_percentage(s)
            if avg < threshold or attendance < 75:
                struggling.append({
                    'student': s,
                    'average': avg,
                    'attendance': attendance,
                    'reason': 'Low grades' if avg < threshold else 'Low attendance',
                })
        return struggling

    @staticmethod
    def get_subject_breakdown(classroom):
        assessments = Assessment.objects.filter(classroom=classroom, is_published=True)
        subjects = {}
        for a in assessments:
            name = a.subject.name if a.subject else 'General'
            if name not in subjects:
                subjects[name] = {'total': 0, 'count': 0}
            subs = AssessmentSubmission.objects.filter(assignment=a, is_graded=True)
            avg = subs.aggregate(avg=Avg('auto_calculated_score'))['avg'] or 0
            subjects[name]['total'] += avg
            subjects[name]['count'] += 1
        result = {}
        for name, data in subjects.items():
            result[name] = round(data['total'] / data['count'], 2) if data['count'] else 0
        return result

    @staticmethod
    def get_performance_trend(classroom, weeks=4):
        trends = []
        for i in range(weeks):
            start = timezone.now() - timedelta(weeks=i + 1)
            end = timezone.now() - timedelta(weeks=i)
            subs = AssessmentSubmission.objects.filter(
                assignment__classroom=classroom,
                is_graded=True,
                graded_at__gte=start,
                graded_at__lt=end,
            )
            avg = subs.aggregate(avg=Avg('auto_calculated_score'))['avg'] or 0
            trends.insert(0, round(avg, 2))
        return trends


class StudentAnalytics:

    @staticmethod
    def get_overall_average(student):
        subs = AssessmentSubmission.objects.filter(student=student, is_graded=True)
        result = subs.aggregate(avg=Avg('auto_calculated_score'))
        return round(result['avg'], 2) if result['avg'] else 0

    @staticmethod
    def get_attendance_percentage(student, days=30):
        cutoff = timezone.now() - timedelta(days=days)
        records = AttendanceRecord.objects.filter(
            student=student, session__session_date__gte=cutoff,
        )
        total = records.count()
        if total == 0:
            return 0
        present = records.filter(status__in=['PRESENT', 'LATE']).count()
        return round((present / total) * 100, 1)

    @staticmethod
    def get_subject_averages(student):
        subs = AssessmentSubmission.objects.filter(student=student, is_graded=True).select_related(
            'assignment__subject',
        )
        subjects = {}
        for s in subs:
            name = s.assignment.subject.name if s.assignment.subject else 'General'
            if name not in subjects:
                subjects[name] = {'total': 0, 'count': 0}
            subjects[name]['total'] += (s.auto_calculated_score or 0)
            subjects[name]['count'] += 1
        result = {}
        for name, data in subjects.items():
            result[name] = round(data['total'] / data['count'], 2) if data['count'] else 0
        return result

    @staticmethod
    def get_performance_trend(student, weeks=4):
        trends = []
        for i in range(weeks):
            start = timezone.now() - timedelta(weeks=i + 1)
            end = timezone.now() - timedelta(weeks=i)
            subs = AssessmentSubmission.objects.filter(
                student=student, is_graded=True,
                graded_at__gte=start, graded_at__lt=end,
            )
            avg = subs.aggregate(avg=Avg('auto_calculated_score'))['avg'] or 0
            trends.insert(0, round(avg, 2))
        return trends

    @staticmethod
    def get_submission_rate(student):
        total_asst = Assessment.objects.filter(
            classroom=student.classroom, is_published=True,
        ).count()
        if total_asst == 0:
            return 0
        submitted = AssessmentSubmission.objects.filter(student=student).count()
        return round((submitted / total_asst) * 100, 1)

    @staticmethod
    def is_at_risk(student):
        avg = StudentAnalytics.get_overall_average(student)
        attendance = StudentAnalytics.get_attendance_percentage(student)
        return avg < 50 or attendance < 75


class TeacherAnalytics:

    @staticmethod
    def get_total_students(teacher):
        classes = teacher.get_assigned_classes()
        return StudentProfile.objects.filter(classroom__in=classes).count()

    @staticmethod
    def get_average_class_performance(teacher):
        classes = teacher.get_assigned_classes()
        if not classes:
            return 0
        total, count = 0, 0
        for c in classes:
            avg = ClassAnalytics.get_average_grade(c)
            if avg:
                total += avg
                count += 1
        return round(total / count, 2) if count else 0

    @staticmethod
    def get_pending_grading_count(teacher):
        return AssessmentSubmission.objects.filter(
            assignment__teacher=teacher,
            is_verified_by_teacher=False,
        ).count()

    @staticmethod
    def get_upcoming_sessions_count(teacher, days=7):
        now = timezone.now()
        end = now + timedelta(days=days)
        return LiveClassSession.objects.filter(
            timetable_slot__teacher=teacher,
            session_date__gte=now,
            session_date__lte=end,
            status__in=['CONFIRMED', 'IN_PROGRESS'],
        ).count()

    @staticmethod
    def get_storage_usage(teacher):
        docs = DocumentShare.objects.filter(owner_teacher=teacher)
        total = docs.aggregate(total=Sum('file_size'))['total'] or 0
        return round(total / (1024 * 1024), 2)
