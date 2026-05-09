from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_admin(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Default admin user created: admin / admin")

class ModelConfig(AppConfig):
    name = 'model'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
