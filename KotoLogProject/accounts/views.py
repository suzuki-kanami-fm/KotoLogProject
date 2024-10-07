from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from accounts.forms import SignupForm, LoginForm, UserEditForm, UserPageForm, ChildForm
from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Family, Child
from django.urls import reverse_lazy,reverse
import uuid

# Create your views here.
class SignupView(View):
    def get(self, request, uuid=None):
        form = SignupForm()

        # UUIDが渡されている場合、家族情報を取得
        family = None
        if uuid:
            family = get_object_or_404(Family, invitation_url__icontains=uuid)

        return render(request, "accounts/signup.html", context={
            "form": form,
            "family": family  # 必要に応じてテンプレートで表示
        })
    
    def post(self, request, uuid=None):
        form = SignupForm(request.POST)

        # UUIDから家族情報を取得
        family = None
        if uuid:
            family = get_object_or_404(Family, invitation_url__icontains=uuid)

        if form.is_valid():
            user = form.save(commit=False)
            
            # 家族が存在する場合はユーザーに関連付ける
            if family:
                user.family_id = family
            
            user.save()
            login(request, user)

            return redirect("home")
        
        return render(request, "accounts/signup.html", context={
            "form": form,
            "family": family 
        })
    

class LoginView(View):
    
    def get(self, request):
        return render(request, "accounts/login.html")
    
    def post(self,request):
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            return redirect("home")
        
        return render(request, "accounts/login.html", context={
            "form": form
        }) 

class LogoutView(LogoutView):
     template_name = "home.html"


class UserEditView(LoginRequiredMixin, View):
    
    def get(self, request):
        user = request.user
        form = UserEditForm(instance=user)
        password_form = PasswordChangeForm(user=request.user)
        return render(request, 'accounts/user_edit.html', {
            'form': form, 
            'user':user,
            "password_form":password_form
        })

    def post(self, request):
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("home")
        return render(request, "accounts/user_edit.html", {"form": form})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_change_form'] = PasswordChangeForm(user=self.request.user)
        return context    


class UserPageView(LoginRequiredMixin, View):
   
    def get(self, request):
        user = request.user
        form = UserPageForm(instance=user)
        
        # 家族情報と子ども情報を取得
        family = user.family_id
        family_members = User.objects.filter(family_id=family).exclude(id=user.id)
        
        # ユーザーまたはその家族に紐づく子どもを取得
        if user.family_id:
            
            children = Child.objects.filter(parent=user) | Child.objects.filter(family=user.family_id).order_by('birthday')
        
        # 家族がない場合は親だけでフィルタリング
        else:
            children = Child.objects.filter(parent=user).order_by('birthday')

        child_form = ChildForm()

        # コンテキストに家族情報、子ども情報、フォームを追加
        context = {
            'form': form,
            'user': user,
            'family_members': family_members,
            'children': children,
            'child_form': child_form,
            'family': family,
        }
        return render(request, "accounts/user_page.html", context)
    
    def post(self, request):
        form = UserPageForm(request.POST, instance=request.user)
    
        # 子ども追加処理
        if 'add_child' in request.POST:
            user = request.user
            child_form = ChildForm(request.POST)
            
            if child_form.is_valid():
                child = child_form.save(commit=False)
                child.parent = request.user
                child.family = request.user.family_id
               
                try:
                    child.save()
                    return redirect('accounts:user_page')
                except Exception as e:
                    child_form.add_error(None, 'エラーが発生しました。再度お試しください。')
                    
             # エラーが発生した場合も、GETと同様に子ども情報を取得して渡す
            if user.family_id:
                children = Child.objects.filter(parent=user) | Child.objects.filter(family=user.family_id).order_by('birthday')
            else:
                children = Child.objects.filter(parent=user).order_by('birthday')
            
            return render(request, 'accounts/user_page.html', {
                'form': form,
                'child_form': child_form,
                'children': children,  # 子ども情報をコンテキストに追加
                'family': user.family_id,
            })
    
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        return render(self.request,"accounts/password_change_done.html" )

class CustomPasswordChangeDoneView(LoginRequiredMixin,PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
    

class InvitationUrlView(LoginRequiredMixin, View):
    
    def get(self, request):
        user = request.user
        family = user.family_id

        # 家族が存在しない場合、エラーを返す
        if not family:
            return render(request, 'accounts/user_page.html', {'message': '家族情報が見つかりません。'})

        # signup_with_inviteのURLにUUIDを追加して招待URLを生成
        invitation_url = request.build_absolute_uri(reverse('accounts:signup_with_invite', kwargs={'uuid': str(uuid.uuid4())}))
        
        # 家族に招待URLを保存
        family.invitation_url = invitation_url
        family.save()

        return render(request, 'accounts/invitation_url.html', {'invitation_url': invitation_url})