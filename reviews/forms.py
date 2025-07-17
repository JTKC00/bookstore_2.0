from django import forms
from .models import Review, ReviewHelpful


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'content']
        widgets = {
            'rating': forms.RadioSelect(choices=Review.RATING_CHOICES, attrs={'required': True}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '評論標題（選填）'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '請分享您對這本書的看法...'
            }),
        }
        labels = {
            'rating': '評分',
            'title': '評論標題',
            'content': '評論內容',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
        self.fields['content'].required = True
        self.fields['rating'].required = True
        self.fields['rating'].choices = Review.RATING_CHOICES  # 這個是為了移除空白選項，因為Django會自動預設確實會有空白選項（如 "--" 或空值）


class ReviewHelpfulForm(forms.ModelForm):
    class Meta:
        model = ReviewHelpful
        fields = ['is_helpful']
        widgets = {
            'is_helpful': forms.HiddenInput(),
        }
