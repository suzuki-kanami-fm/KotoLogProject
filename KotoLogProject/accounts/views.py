from django.shortcuts import render, redirect
from django.views import View
from accounts.forms import SignupForm, LoginForm, UserEditForm, UserPageForm, ChildForm
from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Family, Child
from django.urls import reverse_lazy

# Create your views here.
class SignupView(View):
    
    def get(self, request):
        form = SignupForm()
        return render(request, "accounts/signup.html",context={
            "form":form
        })
    
    def post(self,request):
        print(request.POST)
        form = SignupForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        return render(request, "accounts/signup.html",context={
            "form": form,
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