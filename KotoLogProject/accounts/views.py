from django.shortcuts import render, redirect
from django.views import View
from accounts.forms import SignupForm,LoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView

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
