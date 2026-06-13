from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Document, ChatMessage, QuizAttempt


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'school_name', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'school_name', 'grade_level')}),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'uploaded_at', 'is_processed']
    list_filter = ['is_processed', 'uploaded_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['student', 'question', 'created_at']
    list_filter = ['created_at']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'score', 'total', 'created_at']
    list_filter = ['created_at']
