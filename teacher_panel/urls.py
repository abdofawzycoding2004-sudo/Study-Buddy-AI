from django.urls import path
from . import views

app_name = 'teacher_panel'

urlpatterns = [
    path('analytics/', views.TeacherAnalyticsDashboardView.as_view(), name='analytics'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('course/create/', views.CourseContentBuilderView.as_view(), name='course_create'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:course_pk>/module/create/', views.ModuleCreateView.as_view(), name='module_create'),
    path('module/<int:module_pk>/quiz/create/', views.QuizBuilderView.as_view(), name='quiz_create'),
    path('submissions/', views.GradingCenterListView.as_view(), name='grading_list'),
    path('submission/<int:pk>/grade/', views.GradingCenterUpdateView.as_view(), name='grade_submission'),
    path('course/<int:course_pk>/attendance/', views.AttendanceSheetView.as_view(), name='attendance_sheet'),
]
