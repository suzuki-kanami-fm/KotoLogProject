from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class PortfolioView(View):
    
    def get(self, request):
        return render(request, "portfolio.html")

class HomeView(View):
    
    def get(self, request):
        return render(request, "common/home.html")
    
