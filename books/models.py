from django.db import models

# Create your models here.
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    photo_small = models.ImageField(upload_to="photos/%Y/%m/%d/", blank=True, null=True)
    photo_large = models.ImageField(upload_to="photos/%Y/%m/%d/", blank=True, null=True)
    introduction = models.TextField(blank=True)
    category = models.CharField(max_length=50)
    subcategory = models.CharField(max_length=50)
    language = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_hots = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name="平均評分")
    review_count = models.IntegerField(default=0, verbose_name="評論數量")

    def __str__(self):
        return self.title
    
    def update_average_rating(self):
        """更新平均評分和評論數量"""
        from django.db.models import Avg, Count
        ratings = self.reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        self.average_rating = ratings['avg_rating'] or 0.00
        self.review_count = ratings['count'] or 0
        self.save(update_fields=['average_rating', 'review_count'])
    
    @property
    def rating_stars(self):
        """返回星星顯示"""
        if self.average_rating > 0:
            full_stars = int(self.average_rating)
            half_star = 1 if self.average_rating - full_stars >= 0.5 else 0
            empty_stars = 5 - full_stars - half_star
            return '⭐' * full_stars + ('⭐' if half_star else '') + '☆' * empty_stars
        return '☆☆☆☆☆'
