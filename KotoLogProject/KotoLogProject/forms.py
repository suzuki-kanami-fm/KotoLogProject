from django import forms
from accounts.models import Child

class SearchJournalForm(forms.Form):
    search_query = forms.CharField(
        required=False, 
        label="キーワード", 
        widget=forms.TextInput(attrs={'placeholder': 'キーワード'})
    )
    
    filter_option = forms.ChoiceField(
        choices=[
            ('', 'フィルタを選択'),
            ('public', 'すべて'),
            ('family', '家族'),
            ('favorites', 'お気に入り'),
        ], 
        required=False, 
        label="フィルタ"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        data = kwargs.get('data', None)  # データを取得
        super(SearchJournalForm, self).__init__(*args, **kwargs)

        filter_choices = [
            ('', 'フィルタを選択'),
            ('public', 'すべて'),
            ('family', '家族'),
            ('favorites', 'お気に入り'),
        ]

        if user and user.is_authenticated:
            children = Child.objects.filter(family=user.family)
            for child in children:
                filter_choices.append((str(child.id), f"{child.child_name}の記録"))
        
        self.fields['filter_option'].choices = filter_choices

        # デフォルトの値をフォームに再設定
        if data:
            self.fields['search_query'].initial = data.get('search_query', '')
            self.fields['filter_option'].initial = data.get('filter_option', '')
