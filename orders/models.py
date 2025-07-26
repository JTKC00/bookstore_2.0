from django.db import models
from django.contrib.auth.models import User
from books.models import Book
from carts.models import ShopCart, CartItem
from django.utils import timezone

class Order(models.Model):
    userId = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    shopCartId = models.ForeignKey(ShopCart, on_delete=models.DO_NOTHING)
    invoice_no = models.CharField(max_length=20)
    order_date = models.DateTimeField(auto_now_add=True)
    receipient = models.CharField(max_length=50)
    receipient_phone = models.CharField(max_length=20)
    shipping_address = models.CharField(max_length=200)
    payment_status = models.CharField(max_length=5, choices=[
        ('已付款', '已付款'),
        ('待付款', '待付款'),
    ], default='待付款')
    SHIPPING_STATUS_CHOICES = [
        ('備貨中', '備貨中'),
        ('已出貨', '已出貨'),
        ('已送達', '已送達'),
        ('已取消', '已取消'),
    ]
    shipping_status = models.CharField(max_length=5, choices=SHIPPING_STATUS_CHOICES, default='備貨中')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)  # 使用的優惠碼
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 折扣金額
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 最終金額
    
    def mark_cart_items_as_ordered(self):
        """將此訂單相關的購物車商品標記為已下單"""
        order_items = self.orderitem_set.all()
        for order_item in order_items:
            cart_item = order_item.CartID
            cart_item.is_ordered = True
            cart_item.save()
    
    def clear_cart_after_payment(self):
        """付款成功後清空購物車並記錄優惠碼使用"""
        if self.shopCartId:
            self.mark_cart_items_as_ordered()
            self.shopCartId.clear_ordered_items()
            
        # 如果使用了優惠碼，記錄使用次數
        if self.coupon:
            self.coupon.use_coupon(self.userId)
    
    def apply_coupon(self, coupon_code):
        """應用優惠碼"""
        try:
            # 使用大小寫不敏感的查詢
            coupon = Coupon.objects.get(code__iexact=coupon_code)
            user = self.userId
            
            # 檢查優惠碼是否可以應用於此訂單和用戶
            if not coupon.can_apply_to_order(self.total_amount, user):
                if not coupon.is_valid():
                    return False, "優惠碼無效或已過期"
                elif self.total_amount < coupon.min_order_amount:
                    return False, f"此優惠碼需要最低消費 ${coupon.min_order_amount}，您的訂單金額為 ${self.total_amount}"
                elif coupon.get_user_remaining_uses(user) <= 0:
                    used_count = coupon.get_user_usage_count(user)
                    return False, f"您已使用此優惠碼 {used_count} 次，已達到個人使用上限（{coupon.per_user_limit} 次）"
                else:
                    return False, "優惠碼無法應用於此訂單"
            
            # 應用優惠碼
            self.coupon = coupon
            self.discount_amount = coupon.get_discount_amount(self.total_amount)
            
            # 確保折扣不會超過總金額
            if self.discount_amount > self.total_amount:
                self.discount_amount = self.total_amount
            
            self.final_amount = self.total_amount - self.discount_amount
            self.save()
            
            # 記錄使用（這裡只是保存訂單，實際使用在付款成功後）
            discount_text = f"{coupon.discount}%" if coupon.is_percent else f"${coupon.discount}"
            remaining = coupon.get_user_remaining_uses(user) - 1  # 預期使用後的剩餘次數
            return True, f"優惠碼應用成功！您節省了 ${self.discount_amount} ({discount_text} 折扣)，您還可以使用此優惠碼 {remaining} 次"
            
        except Coupon.DoesNotExist:
            return False, "優惠碼不存在"
    
    def remove_coupon(self):
        """移除優惠碼"""
        self.coupon = None
        self.discount_amount = 0
        self.final_amount = self.total_amount
        self.save()
    
    def get_final_amount(self):
        """獲取最終金額"""
        if self.final_amount is not None:
            return self.final_amount
        return self.total_amount


class OrderItem(models.Model):
    bookid = models.ForeignKey(Book, on_delete=models.DO_NOTHING)
    CartID = models.ForeignKey(CartItem, on_delete=models.DO_NOTHING)
    orderid = models.ForeignKey(Order, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    subTotal = models.DecimalField(max_digits=10, decimal_places=2)

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True) # 優惠碼需要唯一
    discount = models.DecimalField(max_digits=10, decimal_places=2)  # 例如 10.00 代表 $10 或 10%
    is_percent = models.BooleanField(default=False)  # True: 百分比, False: 固定金額
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="最低消費金額才能使用此優惠碼")  # 最低消費金額
    valid_from = models.DateTimeField() # 優惠碼生效時間
    valid_to = models.DateTimeField() # 優惠碼失效時間
    active = models.BooleanField(default=True) # 是否啟用
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="全站總使用次數限制，留空表示無限制") # 全站使用次數限制
    used_count = models.PositiveIntegerField(default=0, help_text="全站已使用次數") # 全站已使用次數
    per_user_limit = models.PositiveIntegerField(default=1, help_text="每個用戶最多可使用次數")  # 每用戶使用次數限制

    def is_valid(self, order_amount=None, user=None):
        """檢查優惠碼是否有效"""
        now = timezone.now() # 當前時間
        
        # 基本有效性檢查：啟用狀態、有效期
        basic_validity = self.active and self.valid_from <= now <= self.valid_to
        
        # 檢查全站使用次數限制（如果有設定的話）
        if self.usage_limit is not None:
            basic_validity = basic_validity and self.used_count < self.usage_limit
        
        # 如果提供了訂單金額，檢查是否滿足最低消費條件
        if order_amount is not None:
            basic_validity = basic_validity and order_amount >= self.min_order_amount
        
        # 如果提供了用戶，檢查該用戶的使用次數限制
        if user is not None and basic_validity:
            user_usage, _ = CouponUsage.objects.get_or_create(
                user=user, 
                coupon=self,
                defaults={'used_count': 0}
            )
            basic_validity = basic_validity and user_usage.can_use_again()
        
        return basic_validity

    def can_apply_to_order(self, order_amount, user=None):
        """檢查優惠碼是否可以應用於指定金額的訂單"""
        return self.is_valid(order_amount, user)

    def use_coupon(self, user=None):
        """使用優惠碼，增加使用次數"""
        if self.is_valid(user=user):
            # 增加全站使用次數（如果有限制的話）
            if self.usage_limit is not None:  # 只有當有設定全站限制才計數
                self.used_count += 1
                self.save()
            
            # 增加用戶個人使用次數
            if user:
                user_usage, created = CouponUsage.objects.get_or_create(
                    user=user, 
                    coupon=self,
                    defaults={'used_count': 0}
                )
                user_usage.used_count += 1
                user_usage.save()
            
            return True
        return False

    def get_user_usage_count(self, user):
        """獲取指定用戶對此優惠碼的使用次數"""
        try:
            usage = CouponUsage.objects.get(user=user, coupon=self)
            return usage.used_count
        except CouponUsage.DoesNotExist:
            return 0

    def get_user_remaining_uses(self, user):
        """獲取指定用戶對此優惠碼的剩餘使用次數"""
        used = self.get_user_usage_count(user)
        return max(0, self.per_user_limit - used)

    def get_discount_amount(self, order_amount):
        """計算折扣金額"""
        if not self.can_apply_to_order(order_amount):
            return 0
        
        if self.is_percent:
            return order_amount * (self.discount / 100)
        else:
            return min(self.discount, order_amount)  # 固定金額不能超過訂單總額

    def __str__(self):
        return self.code


class CouponUsage(models.Model):
    """記錄每個用戶對每個優惠碼的使用情況"""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_count = models.PositiveIntegerField(default=0, help_text="該用戶使用此優惠碼的次數")
    first_used = models.DateTimeField(auto_now_add=True, help_text="首次使用時間")
    last_used = models.DateTimeField(auto_now=True, help_text="最近使用時間")
    
    class Meta:
        unique_together = ('user', 'coupon')  # 確保每個用戶對每個優惠碼只有一條記錄
        verbose_name = "優惠碼使用記錄"
        verbose_name_plural = "優惠碼使用記錄"
    
    def __str__(self):
        return f"{self.user.username} - {self.coupon.code} ({self.used_count}次)"
    
    def can_use_again(self):
        """檢查該用戶是否還能再次使用此優惠碼"""
        return self.used_count < self.coupon.per_user_limit 

