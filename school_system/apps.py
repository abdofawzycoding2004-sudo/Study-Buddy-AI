from django.apps import AppConfig


class SchoolSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'school_system'
    verbose_name = 'School Management System'

    def ready(self):
        import school_system.signals
