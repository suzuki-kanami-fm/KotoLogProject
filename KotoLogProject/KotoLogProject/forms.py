from django import forms
from accounts.models import Child

class SearchJournalForm(forms.Form):
    search_query = forms.CharField(
        required=False, 
        label="", 
        widget=forms.TextInput(attrs={'placeholder': 'キーワード', 'class': 'form-control'})
    )
    
    filter_option = forms.ChoiceField(
        required=False, 
        label="",
        widget=forms.Select(attrs={'class': 'form-select'}),
        choices=[]  # choicesは__init__で動的に設定
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        data = kwargs.get('data', None)  # データを取得
        super(SearchJournalForm, self).__init__(*args, **kwargs)

        # デフォルトのフィルタ選択肢
        filter_choices = [
            ('public', '公開'),
        ]

        # ログイン済みユーザーには追加の選択肢を表示
        if user and user.is_authenticated:
            filter_choices = [
                ('', '公開 + 家族'),
                ('public', '公開'),
                ('family', '家族'),
            ]

            # 子どもごとのフィルタも追加
            children = Child.objects.filter(family=user.family)
            for child in children:
                filter_choices.append((f"child_{child.id}", f"{child.child_name}の記録"))
            
            filter_choices.append(('favorites', 'お気に入り'))

        # フィルタ選択肢を設定
        self.fields['filter_option'].choices = filter_choices

        # 未ログイン時は選択不可
        if not user or not user.is_authenticated:
            self.fields['filter_option'].widget.attrs['disabled'] = 'disabled'

        # デフォルトの値をフォームに再設定
        if data:
            self.fields['search_query'].initial = data.get('search_query', '')
            self.fields['filter_option'].initial = data.get('filter_option', '')
