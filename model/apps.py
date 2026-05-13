from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_admin(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Default admin user created: admin / admin")

def create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    groups = ['Admin', 'Fiscal', 'Supervisor', 'Visualizador']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"Grupo '{group_name}' criado com sucesso.")

def translate_permissions(sender, **kwargs):
    from django.contrib.auth.models import Permission
    translation = {
        'Can add': 'Pode adicionar',
        'Can change': 'Pode alterar',
        'Can delete': 'Pode deletar',
        'Can view': 'Pode visualizar',
    }
    for p in Permission.objects.all():
        for en, pt in translation.items():
            if p.name.startswith(en):
                p.name = p.name.replace(en, pt)
                p.save()

class ModelConfig(AppConfig):
    name = 'model'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
        post_migrate.connect(create_default_groups, sender=self)
        post_migrate.connect(translate_permissions, sender=self)

