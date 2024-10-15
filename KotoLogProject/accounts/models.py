from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta,datetime
import uuid

# Create your models here.

class User(AbstractUser):
    first_name = None
    last_name = None
    date_joined = None
    groups = None
    user_permissions = None
    
    family = models.ForeignKey('Family', on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=100)  # 氏名用
    account_name = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex='^@?[a-zA-Z0-9]+$',
                message='@で始まり、半角英数字のみ入力してください',
                code='invalid_alphanumeric'
            )
        ]
    )
    email = models.EmailField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "account_name" 
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]
    

class Family(models.Model):
    # 複数の招待URLをJSONで管理
    invitations = models.JSONField(default=list, blank=True)  # [{uuid: UUID, expiry: datetime, used: False}, ...]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'families'

    def __str__(self):
        return f"Family: {self.id}"

    def generate_invitation(self):
        #新しい招待URLを生成し、1時間の有効期限を設定
        new_invitation = {
            'uuid': str(uuid.uuid4()),
            'expiry': (timezone.now() + timedelta(hours=1)).isoformat(),
            'used': False
        }
        self.invitations.append(new_invitation)
        self.save()
        return new_invitation

    def validate_invitation(self, uuid):
        #指定されたUUIDが有効かどうか確認
        for invitation in self.invitations:
            if invitation['uuid'] == str(uuid):
                expiry = datetime.fromisoformat(invitation['expiry'])
                
                if not invitation['used'] and expiry > timezone.now():
                    return True
        return False

    def use_invitation(self, uuid):
        #招待URLを使用済みにする
        for invitation in self.invitations:
            if invitation['uuid'] == str(uuid):
                invitation['used'] = True
        self.save()

class Child(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)
    child_name = models.CharField(max_length=100)
    birthday = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'children'
        unique_together = ('family', 'child_name', 'birthday')

    def __str__(self):
        return self.child_name