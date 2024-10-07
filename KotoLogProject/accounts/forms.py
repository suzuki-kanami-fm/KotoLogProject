from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, PasswordChangeForm)
from accounts.models import User
from django.contrib.auth import authenticate

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username","account_name","email"]
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
       
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
               
        return email
    
    def clean_account_name(self):
        account_name = self.cleaned_data.get('account_name')
                
        if User.objects.filter(account_name=account_name).exists():
            raise forms.ValidationError("このアカウント名は既に登録されています。")
        
        return account_name
        
        
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField()
    
    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")
        self.user = authenticate(email=email, password=password)
        
        if self.user is None:
            raise forms.ValidationError("認証に失敗しました")
        
        return self.changed_data

class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["username","account_name","email"]
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance
        
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
               
        return email
    
    def clean_account_name(self):
        account_name = self.cleaned_data.get('account_name')
        user = self.instance       
        if User.objects.filter(account_name=account_name).exclude(pk=user.pk).exists():
            raise forms.ValidationError("このアカウント名は既に登録されています。")
        
        return account_name

class UserPageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['account_name']
