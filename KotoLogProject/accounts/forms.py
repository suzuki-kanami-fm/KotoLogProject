from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, PasswordChangeForm)
from accounts.models import (
    User, Child)
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

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['child_name', 'birthday']
        labels = {
            'child_name': '子どもの名前',
            'birthday': '生年月日',
        }
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        child_name = self.cleaned_data.get('child_name')
        birthday = self.cleaned_data.get('birthday')
        parent = self.instance  #親を取得

        # familyがあるか確認（複数の家族メンバー間での重複チェック）
        family = self.instance.family

        # 同じ名前と生年月日がすでに登録されているか確認
        if Child.objects.filter(child_name=child_name, birthday=birthday, family=family).exists():
            
            raise forms.ValidationError('この名前と生年月日の子どもはすでに登録されています。')

        return cleaned_data        