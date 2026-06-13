from django.contrib import admin
from .models import (
    School, Grade, ClassRoom, Subject,
    TeacherProfile, StudentProfile, TimetableSlot,
    LiveClassSession, AttendanceRecord,
    DocumentShare, DocumentCategory, DocumentAccessLog,
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
    list_display = ['employee_id', 'school', 'experience_years', 'grades_taught', 'classes_taught', 'is_active']
    list_filter = ['school', 'is_active']
    search_fields = ['user__email', 'employee_id']
    filter_horizontal = ['subjects', 'classes']

    def grades_taught(self, obj):
        grade_ids = TimetableSlot.objects.filter(
            teacher=obj, is_active=True
        ).values_list('classroom__grade', flat=True).distinct()
        grades = Grade.objects.filter(id__in=grade_ids)
        return ', '.join(g.name for g in grades) if grades else '—'
    grades_taught.short_description = 'Grades (from slots)'

    def classes_taught(self, obj):
        return ', '.join(str(c) for c in obj.classes.all()) if obj.classes.exists() else '—'
    classes_taught.short_description = 'Classes'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'classroom', 'grade', 'school', 'is_active']
    list_filter = ['school', 'classroom', 'grade', 'is_active']
    search_fields = ['user__email', 'student_id', 'parent_name']


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = [
        'classroom', 'grade_name', 'subject', 'teacher', 'day_of_week',
        'start_time', 'end_time', 'duration_mins', 'is_active',
    ]
    list_filter = ['day_of_week', 'classroom__grade', 'classroom__grade__school', 'is_active']
    search_fields = ['teacher__user__first_name', 'subject__name', 'classroom__name']

    def grade_name(self, obj):
        return obj.classroom.grade.name
    grade_name.short_description = 'Grade'
    grade_name.admin_order_field = 'classroom__grade__name'


@admin.register(LiveClassSession)
class LiveClassSessionAdmin(admin.ModelAdmin):
    list_display = [
        'timetable_slot', 'session_date', 'status',
        'delivery_type', 'attendance_taken',
    ]
    list_filter = ['status', 'delivery_type', 'session_date']
    search_fields = ['timetable_slot__subject__name', 'timetable_slot__classroom__name']
    date_hierarchy = 'session_date'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'check_in_time']
    list_filter = ['status', 'session__session_date']
    search_fields = ['student__user__first_name', 'student__student_id']


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'order']
    list_editable = ['order']


@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'file_size_mb', 'owner_teacher', 'is_public', 'download_count', 'is_active']
    list_filter = ['file_type', 'is_public', 'is_active', 'subject']
    search_fields = ['title', 'owner_teacher__user__first_name']
    filter_horizontal = ['allowed_classes', 'allowed_students']
    readonly_fields = ['download_count', 'view_count', 'file_size', 'mime_type']


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ['document', 'student', 'action', 'accessed_at', 'ip_address']
    list_filter = ['action', 'accessed_at']
    search_fields = ['document__title', 'student__user__first_name']
    readonly_fields = ['document', 'student', 'action', 'accessed_at', 'ip_address', 'user_agent']
