from django.shortcuts import render, redirect
from django.views import View
from accounts.forms import SignupForm, LoginForm, UserEditForm, UserPageForm
from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.forms import PasswordChangeForm

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
        return render(request, "accounts/user_page.html", {'form': form, 'user': user})
    
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        return render(self.request,"accounts/password_change_done.html" )

class CustomPasswordChangeDoneView(LoginRequiredMixin,PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'