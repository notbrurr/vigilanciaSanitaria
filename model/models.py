from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # O C4 Model menciona UserModel com idUsuario, username, passwordHash
    # O AbstractUser do Django já possui id, username e password.
    pass
