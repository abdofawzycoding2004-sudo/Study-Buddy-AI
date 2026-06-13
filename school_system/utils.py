from decimal import Decimal
from django.db.models import Avg
from .models import AssessmentSubmission, Question


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
    def calculate_total_score(submission):
        mcq = AutoGradingEngine.grade_mcq(submission)
        tf = AutoGradingEngine.grade_true_false(submission)
        return mcq + tf

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
        return round((correct / subs.count()) * 100, 1)

    @staticmethod
    def get_student_performance(student):
        subs = AssessmentSubmission.objects.filter(
            student=student, is_graded=True
        )
        result = subs.aggregate(avg=Avg('auto_calculated_score'))
        return round(result['avg'], 2) if result['avg'] else 0
