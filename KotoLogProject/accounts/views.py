from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from accounts.forms import SignupForm, LoginForm, UserEditForm, UserPageForm, ChildForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Family, Child
from django.urls import reverse_lazy,reverse
import uuid
from django.contrib import messages
from django.db import transaction

class SignupView(View):
    
    def get(self, request, uuid=None):
        # UUIDが渡されている場合、対応するFamilyを取得
        family = None
        if uuid:
            family = get_object_or_404(Family)

            # invitationsから手動でUUIDを検索する
            if not family.validate_invitation(uuid):
                messages.error(request, 'この招待URLは無効です。新しい招待URLを発行してください。')
                
                # 無効な場合はホーム画面にリダイレクト
                return redirect('home')  

        # 既にユーザーがログインしている場合、家族登録を実行
        if request.user.is_authenticated:
            if family:
                if not request.user.family:
                    request.user.family = family
                    request.user.save()
                    
                    messages.success(request, '家族登録が完了しました！')
                else:
                    messages.success(request, '家族登録済みのユーザーです。')

                # 招待URLを使用済みにする
                family.use_invitation(uuid)                        
                
                return redirect('accounts:user_page')
        else:
            messages.info(request, 'ログインしてから家族登録を完了してください。')
            login_url = f"{reverse('accounts:login')}?next={request.path}"
            return redirect(login_url)
        
        # 未ログインの場合、サインアップフォームを表示
        form = SignupForm()
        return render(request, "accounts/signup.html", context={"form": form})

    @transaction.atomic  # 招待URL発行の競合を防ぐ
    def post(self, request, uuid=None):
        form = SignupForm(request.POST)

        # UUIDから家族情報を取得
        family = None
        if uuid:
            family = get_object_or_404(Family)

            # UUIDが有効かどうかチェック
            if not family.validate_invitation(uuid):
                messages.error(request, 'この招待URLは無効です。新しい招待URLを発行してください。')
                return redirect('home')  # 無効な場合はホーム画面にリダイレクト

        # 新規登録の場合
        if form.is_valid():
            user = form.save(commit=False)
            
            # 家族が存在する場合はユーザーに関連付ける
            if family:
                user.family = family       

                # 招待URLを使用済みにする
                family.use_invitation(uuid)
                    
            user.save()
            # ユーザーをログインさせる
            login(request, user)

            return redirect("home")

        return render(request, "accounts/signup.html", context={"form": form})

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

class LogoutView(LoginRequiredMixin, LogoutView):
     template_name = "common/home.html"


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
            return redirect("accounts:user_page")
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
        family = user.family
        
        # 家族が存在する場合は家族情報と子ども情報を取得
        if family:
            family_members = User.objects.filter(family=family).exclude(id=user.id)
            children = Child.objects.filter(family=family).order_by('birthday')
        else:
            family_members, children = [], []        

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
        user = request.user
        
        # 子ども追加処理
        if 'add_child' in request.POST:
            child_form = ChildForm(request.POST)
            
            # ユーザーに紐づくFamilyがなければ作成
            if not user.family:
                family = Family.objects.create()
                user.family = family
                user.save()
                        
            if child_form.is_valid():
                child = child_form.save(commit=False)
                child.family = request.user.family
               
                try:
                    child.save()
                    messages.success(request, '子どもが追加されました。')
                    return redirect('accounts:user_page')
                except Exception as e:
                    child_form.add_error(None, 'エラーが発生しました。再度お試しください。')
                                        
            # 家族が存在する場合は家族情報と子ども情報を取得
            if user.family:
                family_members = User.objects.filter(family=user.family).exclude(id=user.id)
                children = Child.objects.filter(family=user.family).order_by('birthday')
            else:
                family_members, children = [], []  
                
            return render(request, 'accounts/user_page.html', {
                'form': form,
                'child_form': child_form,
                'children': children,
                'family': user.family,
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
    
    @transaction.atomic  # 招待URL発行の競合を防ぐ
    def get(self, request):
        user = request.user       
        family = user.family

        # 家族が存在しない場合、新しいFamilyを作成し、ユーザーを関連付ける
        if not family:
            family = Family.objects.create()
            user.family = family
            user.save()

        # 新しい招待URLを発行
        invitation = family.generate_invitation()
        invitation_url = request.build_absolute_uri(reverse('accounts:signup_with_invite', kwargs={'uuid': invitation['uuid']}))
        
        return render(request, 'accounts/invitation_url.html', {'invitation_url': invitation_url})