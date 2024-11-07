from django import forms
from .models import ChildcareJournal
from accounts.models import Child
from django.utils import timezone

class ChildcareJournalForm(forms.ModelForm):
    
    class Meta:
        model = ChildcareJournal
        fields = ['child', 'title', 'published_on', 'content', 'is_public', 'image_url']
        
        labels = {
            'child': '子供選択',
            'title': 'タイトル',
            'published_on': 'いつの出来事？',
            'content': '何が起こった？',
            'is_public': '公開する',
            'image_url': '画像または動画を選択',
        }

        widgets = {
            'child': forms.Select(attrs={'class': 'form-select', 'placeholder': '子供を選択してください'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'タイトル'}),
            'published_on': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': timezone.now().date(),
                'placeholder': '公開日を選択してください'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-label'}),
            'image_url': forms.FileInput(attrs={'class': 'form-control'}),
        }
    # contentフィールドに最大文字数制限を追加
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': '反応、対応策を簡単に記録してください。例: ○○が原因で癇癪を起こしたので、お気に入りのおもちゃで気を紛らわせました。#対応策 #癇癪',
            'maxlength': '2000'
        }),
        max_length=2000,  # 最大2000文字に設定
        label="何が起こった？"
    )        
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ChildcareJournalForm, self).__init__(*args, **kwargs)
        
        # Filter child choices to those related to the user's family
        if user:
            self.fields['child'].queryset = Child.objects.filter(family=user.family)

        self.fields['is_public'].initial = False  # Default to not public
        self.fields['published_on'].initial = timezone.now().date()