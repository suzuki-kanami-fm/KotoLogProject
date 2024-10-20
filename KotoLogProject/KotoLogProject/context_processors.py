from .forms import SearchJournalForm

def search_form(request):
    form = SearchJournalForm(user=request.user if request.user.is_authenticated else None)
    return {'search_form': form}
