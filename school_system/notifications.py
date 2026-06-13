from django.contrib import messages
from django.urls import reverse
from django.utils import timezone


def _notify_students(session, message_text, level=messages.INFO):
    students = session.classroom.get_students().select_related('user')
    for student in students:
        messages.add_message(
            student.user._meta.model.objects.none(),
            level,
            message_text,
        )


def notify_session_confirmed(session):
    day_name = session.timetable_slot.get_day_of_week_display()
    msg = (
        f"Class confirmed: {session.subject.name} for {session.classroom} "
        f"on {session.session_date} ({day_name}) at {session.start_time}."
    )
    _notify_students(session, msg, messages.SUCCESS)


def notify_session_started(session):
    msg = (
        f"Class started: {session.subject.name} for {session.classroom} "
        f"at {session.start_time}."
    )
    if session.delivery_type == 'ONLINE' and session.zoom_join_url:
        msg += f" Join here: {session.zoom_join_url}"

    _notify_students(session, msg, messages.INFO)


def notify_session_cancelled(session):
    msg = (
        f"Class cancelled: {session.subject.name} for {session.classroom} "
        f"on {session.session_date}."
    )
    _notify_students(session, msg, messages.WARNING)
