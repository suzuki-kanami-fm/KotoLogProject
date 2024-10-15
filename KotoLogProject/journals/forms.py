from django import forms
from .models import ChildcareJournal
from django.utils import timezone

class ChildcareJournalForm(forms.ModelForm):
    class Meta:
        model = ChildcareJournal
        fields = ['child', 'title', 'published_on','content', 'is_public',  'image_url']
        
        labels = {
            'child': '子供選択',
            'title': 'タイトル',
            'published_on': 'いつの出来事？',
            'content': '何が起こった？',
            'is_public': '公開する',
            'image_url': '画像または動画を選択',
        }

        widgets = {
            'child': forms.Select(attrs={'placeholder': '子供を選択してください'}),
            'title': forms.TextInput(attrs={'placeholder': 'タイトル'}),
            'published_on':forms.DateInput(attrs={
                'type': 'date',
                'value': timezone.now().date(),  
                'placeholder': '公開日を選択してください'
            }),
            'content': forms.Textarea(attrs={'placeholder': '反応、対応策を簡単に記録してください。例: ○○が原因で癇癪を起こしたので、お気に入りのおもちゃで気を紛らわせました。#対応策 #癇癪'}),
            'is_public': forms.CheckboxInput(),
        }
        
        def __init__(self, *args, **kwargs):
            super(ChildcareJournalForm, self).__init__(*args, **kwargs)
            self.fields['is_public'].initial = False  # 公開しない
            self.fields['published_on'].initial = timezone.now().date() 