from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),
    path('register/student/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
]
