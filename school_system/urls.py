from django.urls import path
from .views_teacher import (
    TimetableView, TimetableSlotCreateView, TimetableSlotUpdateView,
    TimetableSlotDeleteView, LiveClassSessionListView,
    LiveClassSessionCreateView, LiveClassControlView,
    AttendanceManagementView, BulkAttendanceSaveView,
    get_school_subjects, get_grade_classrooms, get_classroom_students,
    AssessmentListView, AssessmentCreateView, AssessmentUpdateView,
    AssessmentDeleteView, AssessmentPublishView,
    QuestionManagementView, QuestionCreateView, QuestionUpdateView,
    QuestionDeleteView,
    AssessmentSubmissionsView, SubmissionDetailView,
    SubmissionGradeView, BulkGradeView,
)
from .views_student import (
    StudentAssessmentListView, StudentAssessmentDetailView,
    StudentAssessmentSubmitView, StudentSubmissionResultView,
)

urlpatterns = [
    path('teacher/timetable/', TimetableView.as_view(), name='teacher_timetable'),
    path('teacher/timetable/create/', TimetableSlotCreateView.as_view(), name='timetable_create'),
    path('teacher/timetable/<int:pk>/update/', TimetableSlotUpdateView.as_view(), name='timetable_update'),
    path('teacher/timetable/<int:pk>/delete/', TimetableSlotDeleteView.as_view(), name='timetable_delete'),
    path('teacher/sessions/', LiveClassSessionListView.as_view(), name='teacher_live_sessions'),
    path('teacher/sessions/create/<int:timetable_slot_id>/', LiveClassSessionCreateView.as_view(), name='live_session_create'),
    path('teacher/sessions/<int:pk>/control/', LiveClassControlView.as_view(), name='live_session_control'),
    path('teacher/sessions/<int:session_id>/attendance/', AttendanceManagementView.as_view(), name='attendance_management'),
    path('teacher/sessions/<int:session_id>/attendance/save/', BulkAttendanceSaveView.as_view(), name='attendance_save'),
    path('api/school-subjects/', get_school_subjects, name='api_school_subjects'),
    path('api/grade-classrooms/', get_grade_classrooms, name='api_grade_classrooms'),
    path('api/classroom-students/', get_classroom_students, name='api_classroom_students'),

    # Assessment (Teacher)
    path('teacher/assessments/', AssessmentListView.as_view(), name='teacher_assessments'),
    path('teacher/assessments/create/', AssessmentCreateView.as_view(), name='assessment_create'),
    path('teacher/assessments/<int:pk>/update/', AssessmentUpdateView.as_view(), name='assessment_update'),
    path('teacher/assessments/<int:pk>/delete/', AssessmentDeleteView.as_view(), name='assessment_delete'),
    path('teacher/assessments/<int:pk>/publish/', AssessmentPublishView.as_view(), name='assessment_publish'),
    path('teacher/assessments/<int:pk>/questions/', QuestionManagementView.as_view(), name='assessment_questions'),
    path('teacher/assessments/<int:assessment_id>/questions/create/', QuestionCreateView.as_view(), name='question_create'),
    path('teacher/assessments/question/<int:pk>/update/', QuestionUpdateView.as_view(), name='question_update'),
    path('teacher/assessments/question/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('teacher/assessments/<int:pk>/submissions/', AssessmentSubmissionsView.as_view(), name='teacher_submissions'),
    path('teacher/assessments/submission/<int:pk>/', SubmissionDetailView.as_view(), name='submission_detail'),
    path('teacher/assessments/submission/<int:pk>/grade/', SubmissionGradeView.as_view(), name='submission_grade'),
    path('teacher/assessments/submissions/bulk-grade/', BulkGradeView.as_view(), name='bulk_grade'),

    # Assessment (Student)
    path('student/assessments/', StudentAssessmentListView.as_view(), name='student_assessments'),
    path('student/assessments/<int:pk>/', StudentAssessmentDetailView.as_view(), name='student_assessment_detail'),
    path('student/assessments/<int:pk>/submit/', StudentAssessmentSubmitView.as_view(), name='student_assessment_submit'),
    path('student/assessments/submission/<int:pk>/result/', StudentSubmissionResultView.as_view(), name='student_submission_result'),
]
