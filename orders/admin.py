from django.contrib import admin
from orders.models import Order, OrderItem, Coupon, CouponUsage
from django.forms import NumberInput  
from django.db import models
from django.utils.html import format_html
from django.utils import timezone
from django.utils import timezone  


## define a class
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "userId",
        "shopCartId",
        "invoice_no",
        "order_date",
        "receipient",
        "receipient_phone",
        "shipping_address",
        "payment_status",
        "shipping_status",
        "total_amount",
        "coupon",
        "discount_amount",
        "final_amount_display",
    )  # Fields to display in the admin list view

    list_display_links = ("id",)  # Fields that are clickable links
    list_filter = ("userId", "payment_status", "shipping_status", "coupon")  # Filters to apply in the admin interface
    list_editable = (
        "payment_status",
        "shipping_status",
    )  # Fields that can be edited directly in the list view
    search_fields = (
        "userId__username",
        "userId__email",
        "invoice_no",
        "receipient",
        "coupon__code",
    )  # Fields to search in the admin interface
    list_per_page = 25  # Number of listings to display per page in the admin interface
    ordering = ["-id"]  # Default ordering of listings by list date in descending order
    ##   title = 'Listings Admin'  # Title for the admin interface
    ##    Example of how to use the slug field
    ##    prepopulated_fields = {'title': ('title',)}  # Automatically populate the slug field based on the title
    ## do not use the slug to insert spaces amid the argument as an endpoint of the URL

    formfield_overrides = {
        models.IntegerField: {"widget": NumberInput(attrs={"size": "10"})}
    }  # Use a number input for DecimalFields
    show_facets = admin.ShowFacets.ALWAYS

    def final_amount_display(self, obj):
        """顯示最終金額，如果有優惠碼則顯示折扣後金額"""
        final_amount = obj.get_final_amount()
        if obj.coupon and obj.discount_amount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${} <small>(已折扣 ${})</small></span>',
                final_amount,
                obj.discount_amount
            )
        return f"${final_amount}"
    final_amount_display.short_description = "最終金額"
    final_amount_display.admin_order_field = "final_amount"


# Register the Listing model with the admin site using the ListingAdmin class
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bookid",
        "bookid__title",
        "orderid",
        "unit_price",
        "quantity",
        "subTotal",
        "CartID",
    )  # Fields to display in the admin list view

    list_display_links = ("id",)  # Fields that are clickable links
    list_filter = ()  # Filters to apply in the admin interface
    list_editable = ()  # Fields that can be edited directly in the list view
    search_fields = (
        "orderid",
        "orderid__invoice_no",
    )  # Fields to search in the admin interface
    list_per_page = 25  # Number of listings to display per page in the admin interface
    ordering = ["-id"]  # Default ordering of listings by list date in descending order
    ##   title = 'Listings Admin'  # Title for the admin interface
    ##    Example of how to use the slug field
    ##    prepopulated_fields = {'title': ('title',)}  # Automatically populate the slug field based on the title
    ## do not use the slug to insert spaces amid the argument as an endpoint of the URL

    formfield_overrides = {
        models.IntegerField: {"widget": NumberInput(attrs={"size": "10"})}
    }  # Use a number input for DecimalFields
    show_facets = admin.ShowFacets.ALWAYS


# Register the Listing model with the admin site using the ListingAdmin class


admin.site.register(Order, OrderAdmin)  # Register the Order model with the admin site
admin.site.register(OrderItem, OrderItemAdmin)


# 優惠碼管理
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_display",
        "min_order_amount",
        "per_user_limit",
        "is_percent", 
        "valid_from",
        "valid_to",
        "active",
        "usage_limit",
        "used_count",
        "remaining_uses",
        "status_display"
    )
    
    list_display_links = ("code",)
    list_filter = ("is_percent", "active", "valid_from", "valid_to")
    list_editable = ("active",)
    search_fields = ("code",)
    list_per_page = 25
    ordering = ["-id"]
    
    # 分組顯示字段
    fieldsets = (
        ('優惠碼基本信息', {
            'fields': ('code', 'discount', 'is_percent', 'min_order_amount'),
            'description': '設定優惠碼名稱、折扣值和最低消費條件。如果是百分比，請勾選"百分比折扣"'
        }),
        ('有效期設定', {
            'fields': ('valid_from', 'valid_to', 'active'),
            'description': '設定優惠碼的有效期間和啟用狀態'
        }),
        ('使用限制', {
            'fields': ('usage_limit', 'used_count', 'per_user_limit'),
            'description': '設定全站總使用次數限制和每用戶使用次數限制。used_count 會自動更新，請勿手動修改'
        }),
    )
    
    # 只讀字段
    readonly_fields = ('used_count',)
    
    # 自定義字段顯示
    def discount_display(self, obj):
        """顯示折扣值"""
        if obj.is_percent:
            return f"{obj.discount}%"
        else:
            return f"${obj.discount}"
    discount_display.short_description = "折扣"
    discount_display.admin_order_field = "discount"
    
    def remaining_uses(self, obj):
        """顯示剩餘使用次數"""
        remaining = obj.usage_limit - obj.used_count
        if remaining <= 0:
            return format_html('<span style="color: red;">已用完</span>')
        elif remaining <= 5:
            return format_html('<span style="color: orange;">{}</span>', remaining)
        else:
            return remaining
    remaining_uses.short_description = "剩餘次數"
    
    def status_display(self, obj):
        """顯示優惠碼狀態"""
        now = timezone.now()
        
        if not obj.active:
            return format_html('<span style="color: gray;">已停用</span>')
        elif obj.used_count >= obj.usage_limit:
            return format_html('<span style="color: red;">已用完</span>')
        elif now < obj.valid_from:
            return format_html('<span style="color: blue;">未開始</span>')
        elif now > obj.valid_to:
            return format_html('<span style="color: red;">已過期</span>')
        else:
            return format_html('<span style="color: green;">可使用</span>')
    status_display.short_description = "狀態"
    
    # 批量操作
    actions = ['activate_coupons', 'deactivate_coupons', 'reset_usage_count']
    
    def activate_coupons(self, request, queryset):
        """批量啟用優惠碼"""
        updated = queryset.update(active=True)
        self.message_user(request, f'成功啟用 {updated} 個優惠碼')
    activate_coupons.short_description = "啟用選中的優惠碼"
    
    def deactivate_coupons(self, request, queryset):
        """批量停用優惠碼"""
        updated = queryset.update(active=False)
        self.message_user(request, f'成功停用 {updated} 個優惠碼')
    deactivate_coupons.short_description = "停用選中的優惠碼"
    
    def reset_usage_count(self, request, queryset):
        """重置使用次數"""
        updated = queryset.update(used_count=0)
        self.message_user(request, f'成功重置 {updated} 個優惠碼的使用次數')
    reset_usage_count.short_description = "重置使用次數"

    formfield_overrides = {
        models.IntegerField: {"widget": NumberInput(attrs={"size": "10"})}
    }
    show_facets = admin.ShowFacets.ALWAYS


# 註冊優惠碼管理
admin.site.register(Coupon, CouponAdmin)


# 優惠碼使用記錄管理
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "coupon",
        "used_count",
        "remaining_uses_display",
        "first_used",
        "last_used",
        "can_use_display"
    )
    
    list_display_links = ("id",)
    list_filter = ("coupon", "first_used", "last_used")
    search_fields = ("user__username", "user__email", "coupon__code")
    readonly_fields = ("first_used", "last_used")
    list_per_page = 25
    ordering = ["-last_used"]
    
    def remaining_uses_display(self, obj):
        """顯示剩餘使用次數"""
        remaining = obj.coupon.per_user_limit - obj.used_count
        if remaining <= 0:
            return format_html('<span style="color: red;">0</span>')
        elif remaining <= 1:
            return format_html('<span style="color: orange;">{}</span>', remaining)
        else:
            return remaining
    remaining_uses_display.short_description = "剩餘次數"
    
    def can_use_display(self, obj):
        """顯示是否還能使用"""
        if obj.can_use_again():
            return format_html('<span style="color: green;">可使用</span>')
        else:
            return format_html('<span style="color: red;">已達上限</span>')
    can_use_display.short_description = "狀態"
    
    # 批量操作
    actions = ['reset_user_usage']
    
    def reset_user_usage(self, request, queryset):
        """重置用戶使用次數"""
        updated = queryset.update(used_count=0)
        self.message_user(request, f'成功重置 {updated} 個用戶的使用記錄')
    reset_user_usage.short_description = "重置選中用戶的使用次數"

# 註冊優惠碼使用記錄管理
admin.site.register(CouponUsage, CouponUsageAdmin)
