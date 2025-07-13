from django import forms
from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['last_name', 'first_name', 'email', 'phone', 'message']  # 移除 'user'
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
        error_messages = {
            'last_name': {'required': '請輸入姓氏'},
            'first_name': {'required': '請輸入名字'},
            'email': {'required': '請輸入電郵'},
            'message': {'required': '請輸入查詢內容'},
        }
    
    def __init__(self, *args, **kwargs):
        # 從 kwargs 取出用戶
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 保存用戶引用供 save 方法使用
        self._user = user
        
        # 如果使用者已登入，自動填充相關欄位
        if user and user.is_authenticated:
            # 設定為隱藏欄位並自動填充值
            self.fields['last_name'].widget = forms.HiddenInput()
            self.fields['last_name'].required = False
            # 優先使用用戶的姓名，如果沒有則使用空字串
            self.fields['last_name'].initial = getattr(user, 'last_name', '') or ''
            
            self.fields['first_name'].widget = forms.HiddenInput()
            self.fields['first_name'].required = False
            # 優先使用用戶的名字，如果沒有則使用用戶名
            self.fields['first_name'].initial = getattr(user, 'first_name', '') or user.username
            
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 如果有關聯的用戶，確保姓名和電郵欄位有值
        if hasattr(self, '_user') and self._user and self._user.is_authenticated:
            if not instance.last_name:
                instance.last_name = getattr(self._user, 'last_name', '') or ''
            if not instance.first_name:
                instance.first_name = getattr(self._user, 'first_name', '') or self._user.username
            if not instance.email:
                instance.email = self._user.email
        
        if commit:
            instance.save()
        return instance