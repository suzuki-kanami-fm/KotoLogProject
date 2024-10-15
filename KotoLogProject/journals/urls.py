from django.urls import path
from .views import (
    ChildcareJournalListView,CreateChildcareJournalView, 
    ChildcareJournalDetailView,EditChildcareJournalView)

app_name='journals'
urlpatterns = [
    path("childcare_journal_list/", ChildcareJournalListView.as_view(), name="childcare_journal_list"),
    path('create_childcare_journal/', CreateChildcareJournalView.as_view(), name='create_childcare_journal'),
    path('journal_detail/<int:journal_id>/', ChildcareJournalDetailView.as_view(), name='journal_detail'),
    path('edit_childcare_journal/<int:journal_id>/', EditChildcareJournalView.as_view(), name='edit_childcare_journal'), 
]