from django.apps import AppConfig


class BackendConfig(AppConfig):
    """Конфиг приложения: при старте подключаются сигналы/почта."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

    def ready(self):
        import backend.signals  # noqa: F401
