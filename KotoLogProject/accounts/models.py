from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.

class User(AbstractUser):
    first_name = None
    last_name = None
    date_joined = None
    groups = None
    user_permissions = None
    
    family_id = models.ForeignKey('Family', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)  # 氏名用
    account_name = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9]+$',
                message='半角英数字のみ入力してください',
                code='invalid_alphanumeric'
            )
        ]
    )
    email = models.EmailField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]
    
from django.db import models

class Family(models.Model):
    invitation_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'families'

    def __str__(self):
        return self.invitation_url

class Child(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    child_name = models.CharField(max_length=100)
    birthday = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'children'

    def __str__(self):
        return self.invitation_url