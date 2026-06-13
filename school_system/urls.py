from django.urls import path, include
from .views_auth import (
    CustomLoginView, CustomLogoutView,
    TeacherRegisterView, StudentRegisterView,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/teacher/', TeacherRegisterView.as_view(), name='teacher_register'),
    path('register/student/', StudentRegisterView.as_view(), name='student_register'),
    path('', include('django.contrib.auth.urls')),
]
