from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from journals.models import ChildcareJournal
from django import forms
from accounts.models import Child
from .forms import SearchJournalForm

# Create your views here.

class PortfolioView(View):
    
    def get(self, request):
        return render(request, "portfolio.html")

class SearchFormView(View):
    
    def get(self, request):
        form = SearchJournalForm(user=request.user)
        print("test",form)
        return render(request, 'common/base.html',{'search_form': form})
