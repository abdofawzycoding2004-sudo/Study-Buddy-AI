from django.contrib import admin
from .models import (
    School, Grade, ClassRoom, Subject,
    TeacherProfile, StudentProfile, TimetableSlot, AttendanceRecord,
)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'country', 'is_active']
    list_filter = ['is_active', 'country', 'city']
    search_fields = ['name', 'code', 'city']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'grade_level', 'academic_year', 'is_active']
    list_filter = ['school', 'academic_year', 'is_active']
    search_fields = ['name', 'school__name']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'current_enrollment', 'capacity', 'class_teacher']
    list_filter = ['grade__school', 'grade', 'is_active']
    search_fields = ['name', 'grade__name']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'is_core_subject', 'schools_list']
    list_filter = ['category', 'is_core_subject', 'schools']
    search_fields = ['name', 'code']
    filter_horizontal = ['schools']

    def schools_list(self, obj):
        return ', '.join(s.code for s in obj.schools.all())
    schools_list.short_description = 'Schools'


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'school', 'experience_years', 'is_active']
    list_filter = ['school', 'is_active']
    search_fields = ['user__email', 'employee_id']
    filter_horizontal = ['subjects']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'classroom', 'grade', 'school', 'is_active']
    list_filter = ['school', 'classroom', 'grade', 'is_active']
    search_fields = ['user__email', 'student_id', 'parent_name']


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'subject', 'teacher', 'day_of_week', 'start_time', 'end_time']
    list_filter = ['day_of_week', 'classroom__grade__school']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'timetable_slot']
    list_filter = ['status', 'date']
    search_fields = ['student__user__first_name', 'student__student_id']
