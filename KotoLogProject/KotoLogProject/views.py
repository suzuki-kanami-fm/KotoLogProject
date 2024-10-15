from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from journals.models import ChildcareJournal

# Create your views here.

class PortfolioView(View):
    
    def get(self, request):
        return render(request, "portfolio.html")



    
