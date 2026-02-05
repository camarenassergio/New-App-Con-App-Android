from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for Logistica Casa Lupita.
    Extends AbstractUser to facilitate future customization.
    """
    pass
