from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import TimetableSlot, LiveClassSession, AttendanceRecord


@receiver(post_save, sender=TimetableSlot)
def create_default_live_sessions(sender, instance, created, **kwargs):
    if not created:
        return

    day_of_week = instance.day_of_week
    today = timezone.localdate()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    first_date = today + timezone.timedelta(days=days_ahead)

    for week in range(4):
        session_date = first_date + timezone.timedelta(weeks=week)
        LiveClassSession.objects.get_or_create(
            timetable_slot=instance,
            session_date=session_date,
            defaults={'status': 'DRAFT'},
        )


@receiver(pre_save, sender=LiveClassSession)
def validate_session_date_matches_day(sender, instance, **kwargs):
    if instance.pk:
        return
    if not instance.session_date:
        return
    if not instance.timetable_slot:
        return

    db_day = instance.session_date.weekday()
    slot_day = instance.timetable_slot.day_of_week

    slot_day_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
    dt_weekday_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}

    if dt_weekday_map.get(db_day) != slot_day_map.get(slot_day):
        raise ValidationError(
            f"Session date ({instance.session_date}) does not match "
            f"timetable slot's day of week ({slot_day})."
        )


@receiver(post_save, sender=AttendanceRecord)
def update_attendance_taken_flag(sender, instance, created, **kwargs):
    session = instance.session
    student_count = session.get_student_count()
    records_count = session.attendance_logs.count()

    if student_count > 0 and records_count >= student_count:
        if not session.attendance_taken:
            session.attendance_taken = True
            session.save(update_fields=['attendance_taken', 'updated_at'])
