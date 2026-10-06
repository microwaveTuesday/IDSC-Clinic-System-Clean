from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = "authentication"

    def ready(self):
        # Import schema extensions after Django app initialization.
        # The import registers them with drf-spectacular.
        from . import schema  # noqa: F401
