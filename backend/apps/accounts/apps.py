from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "accounts"
    name = "apps.accounts"

    def ready(self):
        import apps.accounts.signals  # noqa: F401  (register signal handlers)
