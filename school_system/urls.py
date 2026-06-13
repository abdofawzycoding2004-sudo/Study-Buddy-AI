from django.urls import path
from .views_teacher import (
    TimetableView, TimetableSlotCreateView, TimetableSlotUpdateView,
    TimetableSlotDeleteView, LiveClassSessionListView,
    LiveClassSessionCreateView, LiveClassControlView,
    AttendanceManagementView, BulkAttendanceSaveView,
    ClassRoomCreateView, get_school_subjects,
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
    path('teacher/classroom/create/', ClassRoomCreateView.as_view(), name='teacher_classroom_create'),
    path('api/school-subjects/', get_school_subjects, name='api_school_subjects'),
]
