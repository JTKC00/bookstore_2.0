from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage) 
#等於admin.site.register(ContactMessage, ContactMessageAdmin)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'last_name', 'first_name', 'email', 'created_at', 'user')
    list_filter = ('created_at', 'user')
    search_fields = ('last_name', 'first_name', 'email', 'message')  # 修改這裡：使用實際欄位
    raw_id_fields = ('user',)
    actions = ['remove_duplicates']
    
    def get_name(self, obj):
        """顯示發送者名稱，優先顯示用戶名稱"""
        if obj.user:
            # 顯示用戶名和實際填寫的姓名
            display_name = f"{obj.first_name} {obj.last_name}".strip()
            if display_name:
                return f"{obj.user.username} ({display_name}) ✓"
            else:
                return f"{obj.user.username} ✓"
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else "匿名"
    get_name.short_description = '發送者'
    get_name.admin_order_field = 'user__username'
    
    def remove_duplicates(self, request, queryset):
        """移除重複的查詢記錄"""
        from django.db.models import Count
        
        # 找出重複的記錄
        duplicates = ContactMessage.objects.values('email', 'message').annotate(
            count=Count('id')).filter(count__gt=1)
        
        removed = 0
        for dup in duplicates:
            # 保留最舊的一條記錄
            records = ContactMessage.objects.filter(
                email=dup['email'], 
                message=dup['message']
            ).order_by('created_at')
            
            # 跳過第一條（最舊的），刪除其餘的
            to_delete = list(records)[1:]
            for record in to_delete:
                record.delete()
                removed += 1
        
        self.message_user(request, f"成功移除 {removed} 條重複記錄")
    remove_duplicates.short_description = "移除選中項目中的重複記錄"
