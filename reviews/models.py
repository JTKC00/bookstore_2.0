from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from books.models import Book

User = get_user_model()

class Review(models.Model):
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用戶")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="書籍")
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="評分(1-5)",
        blank=False  # 禁止空白選項
    )
    title = models.CharField(max_length=200, verbose_name="評論標題")
    content = models.TextField(verbose_name="評論內容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="發布時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    is_verified_purchase = models.BooleanField(default=False, verbose_name="已驗證購買")
    
    class Meta:
        verbose_name = "書籍評論"
        verbose_name_plural = "書籍評論"
        unique_together = ('user', 'book')  # 每個用戶對每本書只能評論一次
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating}星)"
    
    @property
    def rating_stars(self):
        """返回星星顯示"""
        return '⭐' * self.rating
    
    def save(self, *args, **kwargs):
        # 檢查用戶是否購買過這本書
        from orders.models import OrderItem
        has_purchased = OrderItem.objects.filter(
            orderid__userId=self.user,
            bookid=self.book,
            orderid__payment_status='paid'
        ).exists()
        self.is_verified_purchase = has_purchased
        super().save(*args, **kwargs)
        
        # 更新書籍的平均評分
        self.book.update_average_rating()


class ReviewHelpful(models.Model):
    """評論有用性投票"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用戶")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes', verbose_name="評論")
    is_helpful = models.BooleanField(verbose_name="是否有用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投票時間")
    
    class Meta:
        verbose_name = "評論有用性投票"
        verbose_name_plural = "評論有用性投票"
        unique_together = ('user', 'review')
    
    def __str__(self):
        helpful_text = "有用" if self.is_helpful else "無用"
        return f"{self.user.username} - {self.review} ({helpful_text})"
